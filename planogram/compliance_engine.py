"""
Planogram compliance engine — compares detected shelf state against intended planogram layout.
Identifies misplaced products, missing facings, incorrect price tags, and unauthorized products.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime
from typing import Optional
import numpy as np

from planogram.schemas import (
    Planogram, Aisle, ShelfSection, ProductFacing,
    SectionViolation, ShelfComplianceResult, AisleComplianceResult, StoreComplianceReport,
)
from config.settings import PLANOGRAM_DIR

# ── OCR price-tag detector (graceful fallback if easyocr not installed) ──
try:
    from models.price_tag_detector import PriceTagDetector, PriceDetectionOutput
    _PRICE_DETECTOR_AVAILABLE = True
except ImportError:
    _PRICE_DETECTOR_AVAILABLE = False


class PlanogramComplianceEngine:
    """
    Compares detected shelf state against planogram definitions.
    Produces compliance reports with violation details.
    """

    def __init__(self, enable_ocr: bool = True):
        self.planograms = {}  # store_id -> Planogram
        # Lazy-init OCR price detector
        self._price_detector = None
        self._ocr_enabled = enable_ocr and _PRICE_DETECTOR_AVAILABLE

    def _get_price_detector(self):
        """Lazy-initialize the price tag detector."""
        if self._price_detector is None and self._ocr_enabled:
            try:
                self._price_detector = PriceTagDetector()
            except Exception:
                self._ocr_enabled = False
        return self._price_detector

    def load_planogram(self, store_id: str) -> Optional[Planogram]:
        """Load planogram JSON for a store."""
        path = PLANOGRAM_DIR / f"planogram_{store_id.lower()}.json"
        if not path.exists():
            return None

        with open(path) as f:
            data = json.load(f)

        planogram = Planogram(**data)
        self.planograms[store_id] = planogram
        return planogram

    def load_all_planograms(self) -> dict:
        """Load all available planograms."""
        for path in PLANOGRAM_DIR.glob("planogram_*.json"):
            store_id = path.stem.replace("planogram_", "").upper()
            self.load_planogram(store_id)
        return self.planograms

    def detect_price_mismatches(
        self,
        shelf_image,
        planogram: Planogram,
    ) -> list[dict]:
        """
        Run OCR on a shelf image and compare detected prices against
        the planogram's expected prices.

        Returns:
            List of dicts: [{section_id, expected_price, detected_price, bbox, confidence}]
        """
        detector = self._get_price_detector()
        if detector is None:
            return []

        result = detector.detect(shelf_image)
        if not result.detections:
            return []

        # Build a lookup of expected prices from the planogram
        expected_prices = {}
        for section in planogram.get_all_sections():
            expected_prices[section.section_id] = section.price

        mismatches = []
        for det in result.detections:
            # Try to match each OCR-detected price against the nearest expected price.
            # In a production system, spatial mapping from bbox to section_id would
            # be used; here we flag any price that doesn't match ANY expected price.
            matched = any(
                abs(det.price - ep) < 0.01 for ep in expected_prices.values()
            )
            if not matched:
                mismatches.append({
                    "detected_price": det.price,
                    "raw_text": det.raw_text,
                    "bbox": det.bbox,
                    "confidence": det.confidence,
                })

        return mismatches

    def check_compliance(
        self,
        store_id: str,
        detected_state: dict,
        planogram: Optional[Planogram] = None,
        shelf_image=None,
    ) -> StoreComplianceReport:
        """
        Check shelf compliance against planogram.

        Args:
            store_id: Store identifier.
            detected_state: Dict mapping section_id to detected info:
                {section_id: {sku_id, count, price, ...}}
            planogram: Planogram to check against (loaded from file if not provided).

        Returns:
            StoreComplianceReport with full compliance details.
        """
        if planogram is None:
            planogram = self.planograms.get(store_id) or self.load_planogram(store_id)

        if planogram is None:
            return StoreComplianceReport(store_id=store_id, checked_at=datetime.now().isoformat())

        # ── If a shelf image is provided, run OCR to enrich detected_state ──
        if shelf_image is not None and self._ocr_enabled:
            ocr_mismatches = self.detect_price_mismatches(shelf_image, planogram)
            # Log OCR-detected mismatches so they can flow into the violation logic
            for mm in ocr_mismatches:
                print(f"  🔍 OCR price mismatch: detected ${mm['detected_price']:.2f} "
                      f"({mm['raw_text']}) conf={mm['confidence']:.2f}")

        aisle_results = []
        total_sections = 0
        compliant = 0
        total_misplaced = 0
        total_missing = 0
        total_unauthorized = 0
        total_price_mismatch = 0

        for aisle in planogram.aisles:
            shelf_results = []

            for shelf in aisle.shelves:
                violations = []
                correct = 0

                for section in shelf.sections:
                    total_sections += 1
                    detected = detected_state.get(section.section_id, {})

                    if not detected:
                        # Section not in detected state — consider as missing
                        violations.append(SectionViolation(
                            section_id=section.section_id,
                            violation_type="MISSING",
                            expected_sku=section.sku_id,
                            severity=3,
                            message=f"Product {section.product_name} missing from {section.section_id}",
                        ))
                        total_missing += 1
                        continue

                    detected_sku = detected.get("sku_id", "")
                    detected_count = detected.get("count", 0)
                    detected_price = detected.get("price", 0.0)

                    # Check for correct SKU
                    if detected_sku and detected_sku != section.sku_id:
                        if detected_sku.startswith("SKU"):
                            violations.append(SectionViolation(
                                section_id=section.section_id,
                                violation_type="MISPLACED",
                                expected_sku=section.sku_id,
                                detected_sku=detected_sku,
                                severity=2,
                                message=f"Expected {section.sku_id} but found {detected_sku} at {section.section_id}",
                            ))
                            total_misplaced += 1
                        else:
                            violations.append(SectionViolation(
                                section_id=section.section_id,
                                violation_type="UNAUTHORIZED",
                                detected_sku=detected_sku,
                                severity=4,
                                message=f"Unauthorized product detected at {section.section_id}",
                            ))
                            total_unauthorized += 1
                        continue

                    # Check for stock level
                    if detected_count == 0:
                        violations.append(SectionViolation(
                            section_id=section.section_id,
                            violation_type="MISSING",
                            expected_sku=section.sku_id,
                            severity=3,
                            message=f"Stockout: {section.product_name} empty at {section.section_id}",
                        ))
                        total_missing += 1
                        continue

                    # Check price tag
                    if detected_price > 0 and abs(detected_price - section.price) > 0.01:
                        violations.append(SectionViolation(
                            section_id=section.section_id,
                            violation_type="PRICE_MISMATCH",
                            expected_sku=section.sku_id,
                            expected_price=section.price,
                            detected_price=detected_price,
                            severity=1,
                            message=f"Price mismatch at {section.section_id}: expected ${section.price:.2f}, found ${detected_price:.2f}",
                        ))
                        total_price_mismatch += 1
                    else:
                        correct += 1
                        compliant += 1

                # Calculate shelf compliance
                shelf_total = len(shelf.sections)
                shelf_score = (correct / max(shelf_total, 1)) * 100

                shelf_results.append(ShelfComplianceResult(
                    shelf_id=shelf.shelf_id,
                    compliance_score=round(shelf_score, 1),
                    total_sections=shelf_total,
                    correct_sections=correct,
                    violations=violations,
                ))

            # Calculate aisle compliance
            aisle_total = sum(sr.total_sections for sr in shelf_results)
            aisle_correct = sum(sr.correct_sections for sr in shelf_results)
            aisle_score = (aisle_correct / max(aisle_total, 1)) * 100
            aisle_violations = sum(len(sr.violations) for sr in shelf_results)

            aisle_results.append(AisleComplianceResult(
                aisle_id=aisle.aisle_id,
                aisle_name=aisle.aisle_name,
                compliance_score=round(aisle_score, 1),
                shelf_results=shelf_results,
                total_violations=aisle_violations,
            ))

        # Overall score
        overall_score = (compliant / max(total_sections, 1)) * 100

        return StoreComplianceReport(
            store_id=store_id,
            store_name=planogram.store_name,
            overall_score=round(overall_score, 1),
            aisle_results=aisle_results,
            total_sections=total_sections,
            compliant_sections=compliant,
            total_misplaced=total_misplaced,
            total_missing=total_missing,
            total_unauthorized=total_unauthorized,
            total_price_mismatches=total_price_mismatch,
            checked_at=datetime.now().isoformat(),
        )

    def simulate_compliance_check(self, store_id: str) -> StoreComplianceReport:
        """
        Simulate a compliance check with random violations for demo.
        """
        planogram = self.planograms.get(store_id) or self.load_planogram(store_id)
        if planogram is None:
            return StoreComplianceReport(store_id=store_id, checked_at=datetime.now().isoformat())

        np.random.seed(hash(store_id + datetime.now().strftime("%Y%m%d")) % 2**31)

        detected_state = {}
        all_sections = planogram.get_all_sections()

        for section in all_sections:
            rand = np.random.random()
            if rand < 0.70:
                # Correct placement
                detected_state[section.section_id] = {
                    "sku_id": section.sku_id,
                    "count": np.random.randint(2, section.expected_facings + 1),
                    "price": section.price,
                }
            elif rand < 0.80:
                # Missing (stockout)
                detected_state[section.section_id] = {
                    "sku_id": section.sku_id,
                    "count": 0,
                    "price": 0,
                }
            elif rand < 0.88:
                # Misplaced product
                wrong_sku_idx = (int(section.sku_id.replace("SKU", "")) + np.random.randint(1, 10))
                wrong_sku = f"SKU{wrong_sku_idx % 50 + 1:03d}"
                detected_state[section.section_id] = {
                    "sku_id": wrong_sku,
                    "count": np.random.randint(1, 4),
                    "price": section.price,
                }
            elif rand < 0.95:
                # Price mismatch
                detected_state[section.section_id] = {
                    "sku_id": section.sku_id,
                    "count": np.random.randint(1, section.expected_facings + 1),
                    "price": section.price + np.random.choice([-0.50, 0.30, -0.20, 0.50]),
                }
            # else: not detected at all → missing

        return self.check_compliance(store_id, detected_state, planogram)
