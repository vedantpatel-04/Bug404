"""
Stock level classifier — determines whether each shelf section is FULL, LOW, or EMPTY
based on product detection density and expected facings.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataclasses import dataclass
from typing import Optional
import numpy as np

from config.settings import STOCK_FULL_THRESHOLD, STOCK_LOW_THRESHOLD


@dataclass
class StockLevelResult:
    """Stock level classification for a shelf section."""
    section_id: str
    stock_level: str  # 'FULL', 'LOW', 'EMPTY'
    fill_ratio: float  # 0.0 to 1.0
    detected_count: int
    expected_count: int
    has_price_tag: bool = True
    price_tag_readable: bool = True


class StockClassifier:
    """
    Classifies shelf section stock levels based on detection density.
    Uses rule-based classification: detected_products / expected_facings → stock level.
    """

    def __init__(
        self,
        full_threshold: float = STOCK_FULL_THRESHOLD,
        low_threshold: float = STOCK_LOW_THRESHOLD,
    ):
        self.full_threshold = full_threshold
        self.low_threshold = low_threshold

    def classify_section(
        self,
        section_id: str,
        detected_count: int,
        expected_count: int,
        has_price_tag: bool = True,
    ) -> StockLevelResult:
        """
        Classify stock level for a single shelf section.

        Args:
            section_id: Unique identifier for the shelf section.
            detected_count: Number of products detected in this section.
            expected_count: Expected number of facings per planogram.
            has_price_tag: Whether a price tag was detected.

        Returns:
            StockLevelResult with classification.
        """
        if expected_count <= 0:
            expected_count = 3  # Default

        fill_ratio = detected_count / expected_count
        fill_ratio = min(fill_ratio, 1.0)

        if fill_ratio >= self.full_threshold:
            level = "FULL"
        elif fill_ratio >= self.low_threshold:
            level = "LOW"
        else:
            level = "EMPTY"

        return StockLevelResult(
            section_id=section_id,
            stock_level=level,
            fill_ratio=round(fill_ratio, 3),
            detected_count=detected_count,
            expected_count=expected_count,
            has_price_tag=has_price_tag,
            price_tag_readable=has_price_tag,
        )

    def classify_shelf(
        self,
        shelf_id: str,
        sections: list,
        expected_facings: Optional[dict] = None,
    ) -> list:
        """
        Classify stock levels for all sections in a shelf.

        Args:
            shelf_id: Shelf identifier.
            sections: List of dicts with 'section_id' and 'detected_count'.
            expected_facings: Dict mapping section_id to expected facing count.

        Returns:
            List of StockLevelResult.
        """
        results = []
        for section in sections:
            sid = section.get("section_id", f"{shelf_id}-{section.get('position', 0)}")
            detected = section.get("detected_count", 0)
            expected = 3  # Default
            if expected_facings and sid in expected_facings:
                expected = expected_facings[sid]
            elif "expected_facings" in section:
                expected = section["expected_facings"]

            result = self.classify_section(
                section_id=sid,
                detected_count=detected,
                expected_count=expected,
                has_price_tag=section.get("has_price_tag", True),
            )
            results.append(result)

        return results

    def get_shelf_summary(self, classifications: list) -> dict:
        """
        Get summary statistics for a set of section classifications.

        Returns:
            Dict with counts and percentages for each stock level.
        """
        total = len(classifications)
        if total == 0:
            return {"total": 0, "full": 0, "low": 0, "empty": 0, "health_score": 0}

        full = sum(1 for c in classifications if c.stock_level == "FULL")
        low = sum(1 for c in classifications if c.stock_level == "LOW")
        empty = sum(1 for c in classifications if c.stock_level == "EMPTY")
        avg_fill = np.mean([c.fill_ratio for c in classifications])

        return {
            "total": total,
            "full": full,
            "low": low,
            "empty": empty,
            "full_pct": round(full / total * 100, 1),
            "low_pct": round(low / total * 100, 1),
            "empty_pct": round(empty / total * 100, 1),
            "avg_fill_ratio": round(avg_fill, 3),
            "health_score": round(avg_fill * 100, 1),
        }

    def simulate_stock_levels(self, store_id: str, num_sections: int = 30) -> list:
        """
        Generate simulated stock level data for demo purposes.

        Returns:
            List of StockLevelResult for random sections.
        """
        np.random.seed(hash(store_id) % 2**31)
        results = []
        for i in range(num_sections):
            section_id = f"{store_id}-A{(i//5)+1:02d}-S{(i%5)+1:02d}-P{(i%3)+1:02d}"
            expected = np.random.choice([3, 4, 5])
            # Weighted random: 60% full, 25% low, 15% empty
            level_type = np.random.choice(["full", "low", "empty"], p=[0.6, 0.25, 0.15])
            if level_type == "full":
                detected = np.random.randint(int(expected * 0.7), expected + 1)
            elif level_type == "low":
                detected = np.random.randint(1, int(expected * 0.5) + 1)
            else:
                detected = 0

            results.append(self.classify_section(
                section_id=section_id,
                detected_count=detected,
                expected_count=expected,
            ))

        return results
