"""
End-to-end shelf analysis pipeline.
Orchestrates: Image → Detection → SKU Recognition → Stock Classification → DB Storage.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np

from models.shelf_detector import ShelfDetector
from models.sku_recognizer import SKURecognizer, SKUReferenceDB
from models.stock_classifier import StockClassifier
from config.settings import SAMPLE_IMAGES_DIR, STORE_CONFIG


@dataclass
class AnalysisResult:
    """Complete result of analyzing a shelf image."""
    store_id: str
    aisle_id: str
    image_path: str
    num_detections: int = 0
    stock_levels: list = field(default_factory=list)
    sku_matches: list = field(default_factory=list)
    shelf_health_score: float = 0.0
    processing_time_ms: float = 0
    timestamp: str = ""
    alerts: list = field(default_factory=list)


class ShelfAnalysisPipeline:
    """
    End-to-end pipeline for analyzing shelf images.
    Processes camera feed frames and produces structured analysis results.
    """

    def __init__(self):
        self.detector = ShelfDetector()
        self.ref_db = SKUReferenceDB()
        self.recognizer = SKURecognizer(self.ref_db)
        self.classifier = StockClassifier()

    def analyze_image(
        self,
        image_path: str,
        store_id: str = "STORE01",
        aisle_id: str = "A01",
        expected_facings: int = 4,
    ) -> AnalysisResult:
        """
        Run full analysis pipeline on a single shelf image.

        Args:
            image_path: Path to the shelf image.
            store_id: Store identifier.
            aisle_id: Aisle identifier.
            expected_facings: Expected products per section.

        Returns:
            AnalysisResult with all findings.
        """
        start_time = time.time()

        # Step 1: Detect products
        detection_result = self.detector.detect_products(image_path)

        # Step 2: Group detections into shelf sections
        sections = self._group_into_sections(
            detection_result.detections,
            detection_result.image_width,
            detection_result.image_height,
        )

        # Step 3: SKU recognition for each detection
        image = cv2.imread(str(image_path))
        sku_matches = []
        if image is not None:
            for det in detection_result.detections:
                matches = self.recognizer.recognize_from_image(image, det.bbox)
                if matches:
                    sku_matches.append({
                        "bbox": det.bbox,
                        "top_match": {
                            "sku_id": matches[0].sku_id,
                            "product_name": matches[0].product_name,
                            "confidence": matches[0].confidence,
                        }
                    })

        # Step 4: Classify stock levels per section
        stock_results = []
        for sec_id, sec_data in sections.items():
            result = self.classifier.classify_section(
                section_id=sec_id,
                detected_count=sec_data["count"],
                expected_count=expected_facings,
            )
            stock_results.append(result)

        # Step 5: Calculate health score
        summary = self.classifier.get_shelf_summary(stock_results)

        # Step 6: Generate alerts for stockouts
        alerts = []
        for sr in stock_results:
            if sr.stock_level == "EMPTY":
                alerts.append({
                    "type": "STOCKOUT",
                    "section_id": sr.section_id,
                    "message": f"Stockout detected at section {sr.section_id}",
                    "severity": 5,
                })
            elif sr.stock_level == "LOW":
                alerts.append({
                    "type": "LOW_STOCK",
                    "section_id": sr.section_id,
                    "message": f"Low stock at section {sr.section_id} ({sr.fill_ratio:.0%} full)",
                    "severity": 3,
                })

        elapsed = (time.time() - start_time) * 1000

        return AnalysisResult(
            store_id=store_id,
            aisle_id=aisle_id,
            image_path=image_path,
            num_detections=detection_result.num_products,
            stock_levels=[{
                "section_id": sr.section_id,
                "stock_level": sr.stock_level,
                "fill_ratio": sr.fill_ratio,
                "detected": sr.detected_count,
                "expected": sr.expected_count,
            } for sr in stock_results],
            sku_matches=sku_matches,
            shelf_health_score=summary.get("health_score", 0),
            processing_time_ms=round(elapsed, 2),
            timestamp=datetime.now().isoformat(),
            alerts=alerts,
        )

    def _group_into_sections(self, detections: list, img_w: int, img_h: int, num_sections: int = 6) -> dict:
        """Group detections into shelf sections based on spatial position."""
        sections = {}
        section_width = img_w / max(num_sections, 1)

        for i in range(num_sections):
            sec_id = f"SEC-{i + 1:02d}"
            sections[sec_id] = {"count": 0, "detections": []}

        for det in detections:
            x = det.bbox[0] + det.bbox[2] / 2  # center x
            sec_idx = int(x / max(section_width, 1))
            sec_idx = min(sec_idx, num_sections - 1)
            sec_id = f"SEC-{sec_idx + 1:02d}"
            sections[sec_id]["count"] += 1
            sections[sec_id]["detections"].append(det)

        return sections

    def analyze_store(self, store_id: str = "STORE01") -> list:
        """
        Analyze all available camera images for a store.

        Returns:
            List of AnalysisResult, one per camera image.
        """
        results = []
        # Look for store-specific images
        store_images = list(SAMPLE_IMAGES_DIR.glob(f"{store_id.lower()}*.png"))
        if not store_images:
            store_images = list(SAMPLE_IMAGES_DIR.glob("store*.png"))[:3]
        if not store_images:
            store_images = list(SAMPLE_IMAGES_DIR.glob("shelf_*.png"))

        for i, img_path in enumerate(store_images):
            result = self.analyze_image(
                image_path=str(img_path),
                store_id=store_id,
                aisle_id=f"A{(i % 6) + 1:02d}",
            )
            results.append(result)

        return results

    def save_results(self, result: AnalysisResult) -> None:
        """Save analysis results to the database."""
        try:
            from database.db_manager import db
            # Store detections
            for sl in result.stock_levels:
                db.insert("detections", {
                    "store_id": result.store_id,
                    "aisle_id": result.aisle_id,
                    "shelf_id": sl["section_id"],
                    "stock_level": sl["stock_level"],
                    "confidence": sl["fill_ratio"],
                    "bbox_x": 0, "bbox_y": 0, "bbox_w": 0, "bbox_h": 0,
                    "image_path": result.image_path,
                })

            # Store alerts
            for alert in result.alerts:
                db.insert("alerts", {
                    "alert_type": alert["type"],
                    "severity": alert["severity"],
                    "store_id": result.store_id,
                    "aisle_id": result.aisle_id,
                    "shelf_id": alert["section_id"],
                    "message": alert["message"],
                    "revenue_impact": np.random.uniform(50, 500),
                    "suggested_action": f"Restock section {alert['section_id']} from backroom",
                    "priority_score": alert["severity"] * np.random.uniform(1, 3),
                })
        except Exception as e:
            print(f"  ⚠ Could not save to database: {e}")


def process_shelf_image(image_path: str, store_id: str = "STORE01", aisle_id: str = "A01") -> dict:
    """
    Convenience function: run a single image through the full pipeline.
    Returns a dict with detections, stock levels, and annotated image path.

    Usage:
        from pipeline.shelf_analysis_pipeline import process_shelf_image
        result = process_shelf_image("path/to/shelf.jpg")
    """
    pipeline = ShelfAnalysisPipeline()
    analysis = pipeline.analyze_image(image_path, store_id=store_id, aisle_id=aisle_id)

    # Also generate annotated image with bounding boxes
    annotated = pipeline.detector.draw_detections(image_path, pipeline.detector.detect_products(image_path))
    annotated_path = str(Path(image_path).parent / f"annotated_{Path(image_path).name}")
    cv2.imwrite(annotated_path, annotated)

    return {
        "analysis": analysis,
        "annotated_image_path": annotated_path,
        "num_detections": analysis.num_detections,
        "health_score": analysis.shelf_health_score,
        "alerts": analysis.alerts,
        "stock_levels": analysis.stock_levels,
    }


if __name__ == "__main__":
    print("Running shelf analysis pipeline...")
    pipeline = ShelfAnalysisPipeline()
    results = pipeline.analyze_store("STORE01")
    for r in results:
        print(f"\n  Image: {Path(r.image_path).name}")
        print(f"  Detections: {r.num_detections}")
        print(f"  Health Score: {r.shelf_health_score}%")
        print(f"  Alerts: {len(r.alerts)}")
        print(f"  Processing: {r.processing_time_ms:.0f}ms")

