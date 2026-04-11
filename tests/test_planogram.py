"""Tests for planogram compliance engine."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
from planogram.schemas import (
    Planogram, Aisle, ShelfSection, ProductFacing,
    SectionViolation, StoreComplianceReport,
)
from planogram.compliance_engine import PlanogramComplianceEngine
from planogram.compliance_scorer import ComplianceScorer


class TestPlanogramSchemas(unittest.TestCase):
    """Tests for Pydantic schema models."""

    def test_product_facing(self):
        pf = ProductFacing(position=1, section_id="A01-S01-P01", sku_id="SKU001", product_name="Test")
        self.assertEqual(pf.sku_id, "SKU001")
        self.assertEqual(pf.expected_facings, 3)

    def test_planogram_total_sections(self):
        planogram = Planogram(
            store_id="TEST",
            store_name="Test Store",
            aisles=[
                Aisle(aisle_id="A01", aisle_name="Aisle 1", shelves=[
                    ShelfSection(shelf_id="S01", shelf_number=1, sections=[
                        ProductFacing(position=1, section_id="P01", sku_id="SKU001", product_name="P1"),
                        ProductFacing(position=2, section_id="P02", sku_id="SKU002", product_name="P2"),
                    ])
                ])
            ]
        )
        self.assertEqual(planogram.total_sections(), 2)


class TestComplianceEngine(unittest.TestCase):
    """Tests for the compliance engine."""

    def setUp(self):
        self.engine = PlanogramComplianceEngine()

    def test_perfect_compliance(self):
        planogram = Planogram(
            store_id="TEST", store_name="Test",
            aisles=[Aisle(aisle_id="A01", aisle_name="Aisle 1", shelves=[
                ShelfSection(shelf_id="S01", shelf_number=1, sections=[
                    ProductFacing(position=1, section_id="P01", sku_id="SKU001", product_name="P1", price=1.99),
                    ProductFacing(position=2, section_id="P02", sku_id="SKU002", product_name="P2", price=2.99),
                ])
            ])]
        )

        detected = {
            "P01": {"sku_id": "SKU001", "count": 3, "price": 1.99},
            "P02": {"sku_id": "SKU002", "count": 3, "price": 2.99},
        }

        report = self.engine.check_compliance("TEST", detected, planogram)
        self.assertEqual(report.overall_score, 100.0)
        self.assertEqual(report.total_misplaced, 0)
        self.assertEqual(report.total_missing, 0)

    def test_misplaced_detection(self):
        planogram = Planogram(
            store_id="TEST", store_name="Test",
            aisles=[Aisle(aisle_id="A01", aisle_name="Aisle 1", shelves=[
                ShelfSection(shelf_id="S01", shelf_number=1, sections=[
                    ProductFacing(position=1, section_id="P01", sku_id="SKU001", product_name="P1", price=1.99),
                ])
            ])]
        )

        detected = {
            "P01": {"sku_id": "SKU005", "count": 3, "price": 1.99},  # Wrong SKU
        }

        report = self.engine.check_compliance("TEST", detected, planogram)
        self.assertEqual(report.total_misplaced, 1)

    def test_stockout_detection(self):
        planogram = Planogram(
            store_id="TEST", store_name="Test",
            aisles=[Aisle(aisle_id="A01", aisle_name="Aisle 1", shelves=[
                ShelfSection(shelf_id="S01", shelf_number=1, sections=[
                    ProductFacing(position=1, section_id="P01", sku_id="SKU001", product_name="P1", price=1.99),
                ])
            ])]
        )

        detected = {
            "P01": {"sku_id": "SKU001", "count": 0, "price": 0},  # Empty
        }

        report = self.engine.check_compliance("TEST", detected, planogram)
        self.assertEqual(report.total_missing, 1)

    def test_simulate_compliance(self):
        self.engine.load_all_planograms()
        if self.engine.planograms:
            store_id = list(self.engine.planograms.keys())[0]
            report = self.engine.simulate_compliance_check(store_id)
            self.assertIsInstance(report, StoreComplianceReport)
            self.assertGreater(report.total_sections, 0)


class TestComplianceScorer(unittest.TestCase):
    """Tests for the compliance scorer."""

    def test_grade_assignment(self):
        scorer = ComplianceScorer()
        report = StoreComplianceReport(
            store_id="TEST", overall_score=92.0,
            total_sections=100, compliant_sections=92,
            total_misplaced=3, total_missing=5,
        )
        details = scorer.calculate_score(report)
        self.assertIn(details["grade"], ["A+", "A", "B+", "B", "C", "D", "F"])

    def test_recommendations(self):
        scorer = ComplianceScorer()
        report = StoreComplianceReport(
            store_id="TEST", overall_score=75.0,
            total_sections=100, compliant_sections=75,
            total_misplaced=10, total_missing=15,
        )
        recs = scorer.generate_recommendations(report)
        self.assertGreater(len(recs), 0)

    def test_trend_simulation(self):
        scorer = ComplianceScorer()
        trend = scorer.simulate_trend_data("STORE01", days=30)
        self.assertEqual(len(trend), 30)
        self.assertIn("compliance_score", trend[0])


if __name__ == "__main__":
    unittest.main()
