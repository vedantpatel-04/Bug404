"""
SKU-level product recognition module.
Matches detected product regions against a reference SKU database
using feature similarity and structural comparison.

Supports two matching backends:
  1. CLIP embeddings (openai/clip-vit-base-patch32) — preferred when available
  2. Color histogram + dominant color — fallback when CLIP is not installed
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import cv2
from dataclasses import dataclass
from typing import Optional

# ── Try importing CLIP; set a flag if unavailable ─────────────────
_CLIP_AVAILABLE = False
_clip_model = None
_clip_preprocess = None

try:
    import torch
    import clip
    from PIL import Image as PILImage
    _CLIP_AVAILABLE = True
except ImportError:
    pass


@dataclass
class SKUMatch:
    """Result of SKU recognition for a detected product region."""
    sku_id: str
    product_name: str
    confidence: float
    method: str  # 'clip', 'color_hist', 'color_hist+dominant'


class SKUReferenceDB:
    """
    Reference database of SKU images and features for matching.
    Stores both color histogram features (always available) and
    CLIP embedding vectors (when CLIP is installed).
    """

    # ── Cosine similarity threshold for CLIP matching ──
    CLIP_SIMILARITY_THRESHOLD = 0.75

    def __init__(self):
        self.references = {}  # sku_id -> {features, color_hist, name, ...}
        self._clip_embeddings = {}  # sku_id -> numpy embedding vector
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

            # Build CLIP embedding for the synthetic reference patch if available
            if _CLIP_AVAILABLE:
                emb = self._compute_clip_embedding(patch)
                if emb is not None:
                    self._clip_embeddings[sku_id] = emb

    # ── CLIP embedding helpers ────────────────────────────────────

    @staticmethod
    def _ensure_clip_model():
        """Lazy-load the CLIP model on first use."""
        global _clip_model, _clip_preprocess
        if _clip_model is not None:
            return True
        if not _CLIP_AVAILABLE:
            return False
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _clip_model, _clip_preprocess = clip.load("ViT-B/32", device=device)
            _clip_model.eval()
            return True
        except Exception as e:
            print(f"  ⚠ Failed to load CLIP model: {e}")
            return False

    @staticmethod
    def _compute_clip_embedding(image_bgr: np.ndarray) -> Optional[np.ndarray]:
        """
        Compute a CLIP embedding vector for a BGR numpy image.
        Returns a normalised 1-D numpy float32 array, or None on failure.
        """
        if not SKUReferenceDB._ensure_clip_model():
            return None
        try:
            # BGR -> RGB -> PIL
            rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
            pil_img = PILImage.fromarray(rgb)
            device = next(_clip_model.parameters()).device
            tensor = _clip_preprocess(pil_img).unsqueeze(0).to(device)
            with torch.no_grad():
                features = _clip_model.encode_image(tensor)
            # L2-normalise so cosine similarity == dot product
            features = features / features.norm(dim=-1, keepdim=True)
            return features.cpu().numpy().flatten().astype(np.float32)
        except Exception:
            return None

    def build_reference_db(self, images_dict: dict) -> int:
        """
        Build / update the CLIP reference embedding database from a dict
        of real product images.

        Args:
            images_dict: {sku_id: numpy BGR image} or {sku_id: list[numpy BGR image]}
                         If a list is provided, embeddings are averaged.

        Returns:
            Number of SKUs successfully embedded.
        """
        count = 0
        for sku_id, img_or_list in images_dict.items():
            imgs = img_or_list if isinstance(img_or_list, list) else [img_or_list]
            embeddings = []
            for img in imgs:
                emb = self._compute_clip_embedding(img)
                if emb is not None:
                    embeddings.append(emb)
            if embeddings:
                # Average and re-normalise
                avg = np.mean(embeddings, axis=0)
                avg = avg / (np.linalg.norm(avg) + 1e-8)
                self._clip_embeddings[sku_id] = avg.astype(np.float32)
                count += 1
        return count

    def get_all_skus(self) -> list:
        return list(self.references.keys())


class SKURecognizer:
    """
    Recognizes SKU-level product identity from cropped detection regions.
    Uses CLIP embeddings when available; falls back to color histogram matching.
    """

    def __init__(self, reference_db: Optional[SKUReferenceDB] = None):
        self.ref_db = reference_db or SKUReferenceDB()
        # Report which backend is active
        if _CLIP_AVAILABLE and self.ref_db._clip_embeddings:
            print("  ✓ SKU recognizer: CLIP embeddings active")
        else:
            print("  ℹ SKU recognizer: using color histogram fallback")

    # ── Public API ────────────────────────────────────────────────

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

        # Try CLIP first; fall back to histogram if it fails or is unavailable
        if _CLIP_AVAILABLE and self.ref_db._clip_embeddings:
            clip_matches = self._clip_recognize(cropped_image, top_k)
            if clip_matches:
                return clip_matches

        # Fallback: color histogram + dominant color matching
        return self._color_histogram_recognize(cropped_image, top_k)

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

    # ── CLIP-based matching ───────────────────────────────────────

    def _clip_recognize(self, cropped_image: np.ndarray, top_k: int) -> list:
        """
        Match a cropped product image against the CLIP reference DB
        using cosine similarity.
        """
        query_emb = self.ref_db._compute_clip_embedding(cropped_image)
        if query_emb is None:
            return []

        matches = []
        for sku_id, ref_emb in self.ref_db._clip_embeddings.items():
            # Cosine similarity (vectors are already L2-normalised)
            similarity = float(np.dot(query_emb, ref_emb))

            # Only consider matches above the threshold
            if similarity < self.ref_db.CLIP_SIMILARITY_THRESHOLD:
                continue

            name = self.ref_db.references.get(sku_id, {}).get("name", sku_id)
            matches.append(SKUMatch(
                sku_id=sku_id,
                product_name=name,
                confidence=round(similarity, 3),
                method="clip",
            ))

        matches.sort(key=lambda m: m.confidence, reverse=True)
        return matches[:top_k]

    # ── Color histogram fallback ──────────────────────────────────

    def _color_histogram_recognize(self, cropped_image: np.ndarray, top_k: int) -> list:
        """
        Original color histogram + dominant color matching.
        Used as fallback when CLIP is not available.
        """
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
