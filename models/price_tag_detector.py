"""
Price Tag Detection via OCR (EasyOCR).
Detects and reads price tags from shelf images, returning structured
price data with bounding boxes and confidence scores.

Falls back gracefully when easyocr is not installed — returns empty results
instead of crashing, so the rest of the pipeline keeps working.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import re
import numpy as np
import cv2
from dataclasses import dataclass, field
from typing import Optional, Union

# ── Try importing EasyOCR; set a flag if unavailable ─────────────────
_EASYOCR_AVAILABLE = False
_reader = None

try:
    import easyocr
    _EASYOCR_AVAILABLE = True
except ImportError:
    pass


@dataclass
class PriceTagResult:
    """A single detected price tag."""
    price: float                # Parsed dollar value, e.g. 4.99
    raw_text: str               # Raw OCR text, e.g. "$4.99"
    bbox: tuple                 # (x, y, w, h) bounding box
    confidence: float           # OCR confidence 0-1


@dataclass
class PriceDetectionOutput:
    """Aggregated results from one image."""
    detections: list = field(default_factory=list)   # list[PriceTagResult]
    processing_time_ms: float = 0.0
    ocr_available: bool = _EASYOCR_AVAILABLE


# ── Regex patterns for prices ────────────────────────────────────────
# Matches formats like $4.99, 4.99, $12, 12.5, ₹199, etc.
_PRICE_PATTERNS = [
    re.compile(r'[\$₹£€]?\s*(\d{1,4}[.,]\d{1,2})'),   # $4.99 or 4.99
    re.compile(r'[\$₹£€]\s*(\d{1,5})'),                 # $12 (integer only)
    re.compile(r'(\d{1,4}[.,]\d{1,2})\s*[\$₹£€]?'),     # 4.99$ (trailing symbol)
]


def _parse_price(text: str) -> Optional[float]:
    """
    Extract a numeric price from raw OCR text.
    Returns None if no valid price pattern is found.
    """
    text = text.strip().replace(',', '.')
    for pat in _PRICE_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                return round(float(m.group(1)), 2)
            except ValueError:
                continue
    return None


class PriceTagDetector:
    """
    Detects price tags in shelf images using EasyOCR.

    Usage:
        detector = PriceTagDetector()
        results  = detector.detect("shelf_image.jpg")
        for r in results.detections:
            print(f"${r.price:.2f} @ {r.bbox}  conf={r.confidence:.2f}")
    """

    def __init__(self, languages: list[str] | None = None, gpu: bool = False):
        """
        Args:
            languages: EasyOCR language codes (default: ['en']).
            gpu:       Whether to use GPU for OCR inference.
        """
        self.languages = languages or ["en"]
        self.gpu = gpu
        self._reader = None
        self._init_attempted = False

    # ── Lazy-init so import never crashes ──────────────────────────
    def _ensure_reader(self) -> bool:
        """Lazily initialize the EasyOCR reader. Returns True if ready."""
        global _reader
        if self._reader is not None:
            return True
        if self._init_attempted:
            return False
        self._init_attempted = True

        if not _EASYOCR_AVAILABLE:
            print("  ⚠ easyocr not installed — price tag detection disabled")
            return False

        try:
            self._reader = easyocr.Reader(self.languages, gpu=self.gpu)
            _reader = self._reader          # cache globally
            return True
        except Exception as e:
            print(f"  ⚠ Failed to initialize EasyOCR reader: {e}")
            return False

    # ── Core detection method ──────────────────────────────────────
    def detect(
        self,
        image: Union[str, Path, np.ndarray],
        min_confidence: float = 0.3,
        preprocess: bool = True,
    ) -> PriceDetectionOutput:
        """
        Detect and read price tags from a shelf image.

        Args:
            image:          File path (str/Path) OR numpy BGR image array.
            min_confidence: Minimum OCR confidence to accept a detection.
            preprocess:     Apply contrast enhancement before OCR.

        Returns:
            PriceDetectionOutput with a list of PriceTagResult entries.
        """
        import time
        t0 = time.time()

        # ── Load image ─────────────────────────────────────────────
        if isinstance(image, (str, Path)):
            img = cv2.imread(str(image))
            if img is None:
                return PriceDetectionOutput(processing_time_ms=0)
        else:
            img = image.copy()

        # ── Optional preprocessing for better OCR accuracy ─────────
        if preprocess:
            img = self._preprocess(img)

        # ── Run OCR ────────────────────────────────────────────────
        if not self._ensure_reader():
            # Fallback: return empty result without crashing
            return PriceDetectionOutput(
                processing_time_ms=round((time.time() - t0) * 1000, 2),
                ocr_available=False,
            )

        try:
            ocr_results = self._reader.readtext(img)
        except Exception as e:
            print(f"  ⚠ OCR inference failed: {e}")
            return PriceDetectionOutput(
                processing_time_ms=round((time.time() - t0) * 1000, 2),
            )

        # ── Parse OCR results into structured price data ──────────
        detections = []
        for bbox_pts, text, conf in ocr_results:
            if conf < min_confidence:
                continue

            price = _parse_price(text)
            if price is None:
                continue        # Not a price — skip

            # Convert EasyOCR polygon to (x, y, w, h)
            xs = [pt[0] for pt in bbox_pts]
            ys = [pt[1] for pt in bbox_pts]
            x, y = int(min(xs)), int(min(ys))
            w, h = int(max(xs) - x), int(max(ys) - y)

            detections.append(PriceTagResult(
                price=price,
                raw_text=text.strip(),
                bbox=(x, y, w, h),
                confidence=round(float(conf), 3),
            ))

        elapsed = round((time.time() - t0) * 1000, 2)
        return PriceDetectionOutput(
            detections=detections,
            processing_time_ms=elapsed,
            ocr_available=True,
        )

    # ── Image preprocessing for OCR ────────────────────────────────
    @staticmethod
    def _preprocess(img: np.ndarray) -> np.ndarray:
        """
        Enhance contrast and sharpness for price tag readability.
        """
        # Convert to grayscale for OCR (higher accuracy)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # CLAHE for adaptive contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Mild sharpening kernel to make digits crisper
        sharpen_kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0],
        ], dtype=np.float32)
        enhanced = cv2.filter2D(enhanced, -1, sharpen_kernel)

        # Adaptive threshold to isolate text from label background
        binary = cv2.adaptiveThreshold(
            enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=11,
            C=2,
        )

        return binary

    # ── Convenience: detect from a cropped region ──────────────────
    def detect_in_region(
        self,
        image: np.ndarray,
        roi: tuple,
        min_confidence: float = 0.3,
    ) -> PriceDetectionOutput:
        """
        Detect prices in a specific region of interest.

        Args:
            image: Full shelf image (BGR numpy array).
            roi:   (x, y, w, h) bounding box of the region to scan.

        Returns:
            PriceDetectionOutput for that region only.
        """
        x, y, w, h = roi
        crop = image[y:y + h, x:x + w]
        result = self.detect(crop, min_confidence=min_confidence)

        # Offset bboxes back to full-image coordinates
        for det in result.detections:
            dx, dy, dw, dh = det.bbox
            det.bbox = (dx + x, dy + y, dw, dh)

        return result

    # ── Visualization helper ───────────────────────────────────────
    def draw_prices(
        self,
        image: np.ndarray,
        detections: list,
    ) -> np.ndarray:
        """
        Draw detected price tags on the image for debugging / dashboard.
        """
        out = image.copy()
        for det in detections:
            x, y, w, h = det.bbox
            # Green box for detected price
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
            label = f"${det.price:.2f} ({det.confidence:.0%})"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(out, (x, y - lh - 8), (x + lw + 4, y), (0, 255, 0), -1)
            cv2.putText(out, label, (x + 2, y - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        return out
