"""Tests for shelf detector module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
from models.shelf_detector import ShelfDetector, Detection, ShelfDetectionResult


class TestShelfDetector(unittest.TestCase):
    """Tests for the ShelfDetector class."""

    def setUp(self):
        self.detector = ShelfDetector()

    def test_detector_initialization(self):
        """Test that detector initializes without crashing."""
        self.assertIsNotNone(self.detector)
        self.assertIsInstance(self.detector.confidence, float)

    def test_detection_dataclass(self):
        """Test Detection dataclass creation."""
        det = Detection(
            bbox=(10, 20, 50, 100),
            confidence=0.85,
            class_id=0,
            class_name="product_0",
        )
        self.assertEqual(det.bbox, (10, 20, 50, 100))
        self.assertAlmostEqual(det.confidence, 0.85)
        self.assertEqual(det.class_name, "product_0")

    def test_detection_result_dataclass(self):
        """Test ShelfDetectionResult creation."""
        result = ShelfDetectionResult(image_path="test.png")
        self.assertEqual(result.image_path, "test.png")
        self.assertEqual(result.num_products, 0)
        self.assertIsInstance(result.detections, list)

    def test_preprocess_image(self):
        """Test image preprocessing."""
        # Create a simple test image
        test_img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = self.detector.preprocess_image(test_img)
        self.assertEqual(result.shape, test_img.shape)

    def test_synthetic_detect(self):
        """Test synthetic detection on a colored image."""
        # Create image with colored blocks
        img = np.ones((200, 300, 3), dtype=np.uint8) * 230
        # Add colored rectangles
        img[20:80, 30:60] = [0, 0, 200]  # Red product
        img[20:80, 70:100] = [0, 200, 0]  # Green product
        img[20:80, 110:140] = [200, 0, 0]  # Blue product

        detections = self.detector._synthetic_detect(img, 300, 200)
        self.assertIsInstance(detections, list)
        # Should detect some products
        for det in detections:
            self.assertIsInstance(det, Detection)
            self.assertGreater(det.confidence, 0)

    def test_detect_nonexistent_image(self):
        """Test detection on a non-existent image returns empty result."""
        result = self.detector.detect_products("nonexistent_image.png")
        self.assertEqual(result.num_products, 0)

    def test_batch_detect(self):
        """Test batch detection."""
        results = self.detector.detect_batch(["fake1.png", "fake2.png"])
        self.assertEqual(len(results), 2)


class TestDetectionOnSampleImages(unittest.TestCase):
    """Integration tests with sample images."""

    def test_detect_on_sample_images(self):
        """Test detection on generated sample images."""
        from config.settings import SAMPLE_IMAGES_DIR
        images = list(SAMPLE_IMAGES_DIR.glob("*.png"))
        if not images:
            self.skipTest("No sample images found — run seed_data.py first")

        detector = ShelfDetector()
        result = detector.detect_products(str(images[0]))
        self.assertIsInstance(result, ShelfDetectionResult)
        self.assertGreater(result.image_width, 0)
        self.assertGreater(result.image_height, 0)


if __name__ == "__main__":
    unittest.main()
