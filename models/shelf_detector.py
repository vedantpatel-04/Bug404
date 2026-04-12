"""
YOLOv8-based shelf product detector.
Uses Ultralytics YOLOv8 for detecting products on retail shelves.
Supports preprocessing for varying lighting and camera angles.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import cv2
from dataclasses import dataclass, field
from typing import Optional

from config.settings import (
    YOLO_MODEL, DETECTION_CONFIDENCE, DETECTION_IOU_THRESHOLD,
    IMAGE_SIZE, WEIGHTS_DIR
)


@dataclass
class Detection:
    """Single object detection result."""
    bbox: tuple  # (x, y, w, h)
    confidence: float
    class_id: int
    class_name: str
    shelf_region: int = -1
    section_region: int = -1


@dataclass
class ShelfDetectionResult:
    """Complete detection result for a shelf image."""
    image_path: str
    detections: list = field(default_factory=list)
    num_products: int = 0
    processing_time_ms: float = 0
    image_width: int = 0
    image_height: int = 0


class ShelfDetector:
    """
    YOLOv8-based product detector for retail shelf images.
    Loads custom-trained weights (shelfiq_best.pt) when available,
    falls back to generic yolov8n.pt, then to synthetic mode.
    """

    def __init__(self, model_path: Optional[str] = None, confidence: float = DETECTION_CONFIDENCE):
        self.confidence = confidence
        self.iou_threshold = DETECTION_IOU_THRESHOLD
        self.model = None
        self.use_synthetic = False

        # Resolve model path: explicit arg → config → fallback
        resolved_path = model_path or YOLO_MODEL
        custom_weights = WEIGHTS_DIR.parent / "weights" / "shelfiq_best.pt"
        if not model_path and custom_weights.exists():
            resolved_path = str(custom_weights)

        # Try to load YOLO model
        try:
            from ultralytics import YOLO
            self.model = YOLO(resolved_path)
            is_custom = "shelfiq" in str(resolved_path).lower()
            tag = "CUSTOM-TRAINED" if is_custom else "PRE-TRAINED"
            print(f"  ✓ YOLOv8 model loaded [{tag}]: {resolved_path}")
        except Exception as e:
            print(f"  ⚠ YOLOv8 not available ({e}), using synthetic detection mode")
            self.use_synthetic = True

    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Apply preprocessing to handle varying lighting conditions."""
        # Convert to LAB color space for better contrast handling
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)

        # Merge back and convert to BGR
        enhanced = cv2.merge([l_enhanced, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

        # Slight Gaussian blur to reduce noise
        enhanced = cv2.GaussianBlur(enhanced, (3, 3), 0)

        return enhanced

    def detect_products(self, image_path: str) -> ShelfDetectionResult:
        """
        Detect products in a shelf image.

        Args:
            image_path: Path to shelf image file.

        Returns:
            ShelfDetectionResult with all detections.
        """
        import time
        start_time = time.time()

        image = cv2.imread(str(image_path))
        if image is None:
            return ShelfDetectionResult(image_path=image_path)

        h, w = image.shape[:2]
        preprocessed = self.preprocess_image(image)

        if self.use_synthetic:
            detections = self._synthetic_detect(preprocessed, w, h)
        else:
            detections = self._yolo_detect(preprocessed)

        elapsed = (time.time() - start_time) * 1000

        # Assign shelf regions based on y-coordinate
        if detections:
            y_positions = [d.bbox[1] for d in detections]
            if y_positions:
                min_y, max_y = min(y_positions), max(y_positions)
                shelf_height = (max_y - min_y) / 4 if max_y > min_y else h / 4
                for d in detections:
                    d.shelf_region = int((d.bbox[1] - min_y) / max(shelf_height, 1))

        return ShelfDetectionResult(
            image_path=image_path,
            detections=detections,
            num_products=len(detections),
            processing_time_ms=round(elapsed, 2),
            image_width=w,
            image_height=h,
        )

    def _yolo_detect(self, image: np.ndarray) -> list:
        """Run YOLOv8 inference."""
        results = self.model(image, conf=self.confidence, iou=self.iou_threshold, imgsz=IMAGE_SIZE, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])
                cls_name = self.model.names.get(cls_id, f"class_{cls_id}")
                detections.append(Detection(
                    bbox=(int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                    confidence=round(conf, 3),
                    class_id=cls_id,
                    class_name=cls_name,
                ))
        return detections

    def detect_frame(self, frame: np.ndarray) -> ShelfDetectionResult:
        """
        Run detection on a raw video frame (numpy array) without file I/O.
        Ideal for real-time video processing.

        Args:
            frame: BGR numpy array from cv2.VideoCapture.

        Returns:
            ShelfDetectionResult with all detections.
        """
        import time
        start_time = time.time()

        h, w = frame.shape[:2]
        preprocessed = self.preprocess_image(frame)

        if self.use_synthetic:
            detections = self._synthetic_detect(preprocessed, w, h)
        else:
            detections = self._yolo_detect(preprocessed)

        elapsed = (time.time() - start_time) * 1000

        # Assign shelf regions based on y-coordinate
        if detections:
            y_positions = [d.bbox[1] for d in detections]
            if y_positions:
                min_y, max_y = min(y_positions), max(y_positions)
                shelf_height = (max_y - min_y) / 4 if max_y > min_y else h / 4
                for d in detections:
                    d.shelf_region = int((d.bbox[1] - min_y) / max(shelf_height, 1))

        return ShelfDetectionResult(
            image_path="<live_frame>",
            detections=detections,
            num_products=len(detections),
            processing_time_ms=round(elapsed, 2),
            image_width=w,
            image_height=h,
        )

    def _synthetic_detect(self, image: np.ndarray, w: int, h: int) -> list:
        """
        Synthetic detection using color segmentation.
        Used when YOLO model is not available.
        """
        detections = []
        # Convert to HSV
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Detect colored product regions via contour analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilated = cv2.dilate(edges, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        product_id = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500 or area > w * h * 0.15:
                continue

            x, y, cw, ch = cv2.boundingRect(contour)
            aspect_ratio = ch / max(cw, 1)

            # Products are typically taller than wide
            if 0.5 < aspect_ratio < 5.0:
                confidence = min(0.95, 0.5 + (area / (w * h)) * 5)
                detections.append(Detection(
                    bbox=(x, y, cw, ch),
                    confidence=round(confidence, 3),
                    class_id=product_id % 10,
                    class_name=f"product_{product_id}",
                ))
                product_id += 1

        return detections

    def detect_batch(self, image_paths: list) -> list:
        """Run detection on multiple images."""
        return [self.detect_products(p) for p in image_paths]

    def draw_detections(self, image_path: str, result: ShelfDetectionResult) -> np.ndarray:
        """Draw detection bounding boxes on image for visualization."""
        image = cv2.imread(str(image_path))
        if image is None:
            return np.zeros((100, 100, 3), dtype=np.uint8)

        colors = [
            (0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0),
            (255, 0, 255), (0, 255, 255), (128, 255, 0), (255, 128, 0),
        ]

        for i, det in enumerate(result.detections):
            x, y, w, h = det.bbox
            color = colors[det.class_id % len(colors)]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

            label = f"{det.class_name} {det.confidence:.2f}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
            cv2.rectangle(image, (x, y - lh - 6), (x + lw, y), color, -1)
            cv2.putText(image, label, (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return image
