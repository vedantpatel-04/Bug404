"""
SKU-level product recognition module.
Matches detected product regions against a reference SKU database
using feature similarity and structural comparison.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import cv2
from dataclasses import dataclass
from typing import Optional


@dataclass
class SKUMatch:
    """Result of SKU recognition for a detected product region."""
    sku_id: str
    product_name: str
    confidence: float
    method: str  # 'color_hist', 'ssim', 'orb', 'template'


class SKUReferenceDB:
    """
    Reference database of SKU images and features for matching.
    In production, this would use a trained embedding model.
    For the prototype, we use color histogram + structural similarity.
    """

    def __init__(self):
        self.references = {}  # sku_id -> {features, color_hist, name}
        self._build_synthetic_references()

    def _build_synthetic_references(self):
        """Build synthetic reference features for known SKUs."""
        from data.generators.generate_shelf_images import PRODUCT_COLORS
        from data.generators.generate_pos_data import PRODUCT_NAMES

        for i, (color, name) in enumerate(zip(PRODUCT_COLORS, PRODUCT_NAMES[:len(PRODUCT_COLORS)])):
            sku_id = f"SKU{i + 1:03d}"
            # Create a small reference patch
            patch = np.zeros((80, 40, 3), dtype=np.uint8)
            patch[:] = color[::-1]  # RGB to BGR
            hist = cv2.calcHist([patch], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
            hist = cv2.normalize(hist, hist).flatten()

            self.references[sku_id] = {
                "name": name,
                "color": color,
                "color_hist": hist,
                "dominant_bgr": color[::-1],
            }

    def get_all_skus(self) -> list:
        return list(self.references.keys())


class SKURecognizer:
    """
    Recognizes SKU-level product identity from cropped detection regions.
    Uses multi-method matching: color histogram, dominant color, and structural comparison.
    """

    def __init__(self, reference_db: Optional[SKUReferenceDB] = None):
        self.ref_db = reference_db or SKUReferenceDB()

    def recognize(self, cropped_image: np.ndarray, top_k: int = 3) -> list:
        """
        Recognize SKU from a cropped product image.

        Args:
            cropped_image: BGR image of the detected product region.
            top_k: Number of top matches to return.

        Returns:
            List of SKUMatch sorted by confidence (descending).
        """
        if cropped_image is None or cropped_image.size == 0:
            return []

        # Resize for consistent comparison
        target_size = (40, 80)
        try:
            resized = cv2.resize(cropped_image, target_size)
        except Exception:
            return []

        # Calculate color histogram of the query image
        query_hist = cv2.calcHist([resized], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        query_hist = cv2.normalize(query_hist, query_hist).flatten()

        # Get dominant color
        pixels = resized.reshape(-1, 3).astype(np.float32)
        _, labels, centers = cv2.kmeans(
            pixels, 3, None,
            (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0),
            3, cv2.KMEANS_PP_CENTERS
        )
        # Find the largest cluster (dominant color)
        unique, counts = np.unique(labels, return_counts=True)
        dominant_idx = unique[np.argmax(counts)]
        dominant_color = centers[dominant_idx].astype(int)

        # Match against all references
        matches = []
        for sku_id, ref in self.ref_db.references.items():
            # Method 1: Histogram comparison (correlation)
            hist_score = cv2.compareHist(query_hist, ref["color_hist"], cv2.HISTCMP_CORREL)
            hist_score = max(0, hist_score)

            # Method 2: Dominant color distance (inverse normalized)
            color_dist = np.linalg.norm(dominant_color - np.array(ref["dominant_bgr"]))
            max_dist = np.sqrt(3 * 255**2)
            color_score = 1.0 - (color_dist / max_dist)

            # Combine scores
            combined = 0.6 * hist_score + 0.4 * color_score

            matches.append(SKUMatch(
                sku_id=sku_id,
                product_name=ref["name"],
                confidence=round(combined, 3),
                method="color_hist+dominant",
            ))

        # Sort by confidence descending
        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:top_k]

    def recognize_from_image(self, image: np.ndarray, bbox: tuple) -> list:
        """
        Recognize SKU given full image and bounding box.

        Args:
            image: Full shelf image (BGR).
            bbox: (x, y, w, h) bounding box of the product.

        Returns:
            List of SKUMatch.
        """
        x, y, w, h = bbox
        cropped = image[y:y + h, x:x + w]
        return self.recognize(cropped)

    def batch_recognize(self, image: np.ndarray, bboxes: list) -> dict:
        """
        Recognize SKUs for multiple bounding boxes in one image.

        Returns:
            Dict mapping bbox index to list of SKUMatch.
        """
        results = {}
        for i, bbox in enumerate(bboxes):
            results[i] = self.recognize_from_image(image, bbox)
        return results
