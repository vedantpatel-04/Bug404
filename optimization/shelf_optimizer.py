"""
AI Shelf Arrangement Optimizer.

Implements a complete ML pipeline for optimizing retail shelf layouts:
  1. DataIngestor     — pulls sales + engagement data from SQLite / CSV
  2. FeatureEngineer  — computes per-SKU velocity, profit, engagement, composite score
  3. ShelfPlacementOptimizer — greedy tier-based placement algorithm
  4. PlanogramBuilder — maps placement decisions into Pydantic planogram objects
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import math
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import numpy as np

from config.settings import (
    DATABASE_PATH,
    POS_DATA_DIR,
    STORE_CONFIG,
    CATEGORIES,
    EYE_LEVEL_SHELVES,
    TOP_PERFORMER_PERCENTILE,
    ENGAGEMENT_DATA_PATH,
    OPTIMIZER_OUTPUT_DIR,
    SCORE_WEIGHT_VELOCITY,
    SCORE_WEIGHT_PROFIT,
    SCORE_WEIGHT_ENGAGEMENT,
    SHELF_VISIBILITY_MULTIPLIER,
)
from planogram.schemas import Planogram, Aisle, ShelfSection, ProductFacing


# ═══════════════════════════════════════════════════════════════
#  Data Classes
# ═══════════════════════════════════════════════════════════════

@dataclass
class SKUMetrics:
    """Aggregated metrics for a single SKU."""
    sku_id: str
    product_name: str
    category: str
    unit_price: float
    total_quantity: int = 0
    total_revenue: float = 0.0
    sales_velocity: float = 0.0        # units per week
    profit_contribution: float = 0.0
    impression_count: int = 0
    pick_count: int = 0
    conversion_rate: float = 0.0
    engagement_score: float = 0.0
    composite_score: float = 0.0
    tier: str = "Standard"              # Premium / Standard / Economy


@dataclass
class PlacementSlot:
    """A single slot on a shelf that can hold a product."""
    aisle_idx: int
    shelf_number: int
    section_number: int
    aisle_id: str = ""
    shelf_id: str = ""
    section_id: str = ""
    assigned_sku: Optional[SKUMetrics] = None


# ═══════════════════════════════════════════════════════════════
#  Stage 1: Data Ingestion
# ═══════════════════════════════════════════════════════════════

class DataIngestor:
    """Pulls aggregated sales and engagement data."""

    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path

    def get_sales_summary(self, store_id: str) -> pd.DataFrame:
        """
        Pull aggregated sales from pos_transactions.

        Returns DataFrame with columns:
            sku_id, product_name, category, unit_price,
            total_quantity, total_revenue, num_days
        """
        conn = sqlite3.connect(str(self.db_path))
        query = """
            SELECT
                pt.sku_id,
                pt.product_name,
                pt.category,
                AVG(pt.unit_price)  AS unit_price,
                SUM(pt.quantity_sold) AS total_quantity,
                SUM(pt.revenue)       AS total_revenue,
                COUNT(DISTINCT pt.date) AS num_days
            FROM pos_transactions pt
            WHERE pt.store_id = ?
            GROUP BY pt.sku_id, pt.product_name, pt.category
            ORDER BY total_revenue DESC
        """
        df = pd.read_sql_query(query, conn, params=(store_id,))
        conn.close()
        return df

    def get_engagement_data(self, store_id: str) -> pd.DataFrame:
        """
        Pull engagement data from SQLite or fall back to CSV.

        Returns DataFrame with columns:
            sku_id, impression_count, pick_count, conversion_rate
        """
        # Try database first
        conn = sqlite3.connect(str(self.db_path))
        try:
            query = """
                SELECT sku_id, impression_count, pick_count, conversion_rate
                FROM customer_engagement
                WHERE store_id = ?
            """
            df = pd.read_sql_query(query, conn, params=(store_id,))
            if not df.empty:
                conn.close()
                return df
        except Exception:
            pass
        finally:
            conn.close()

        # Fallback to CSV
        if ENGAGEMENT_DATA_PATH.exists():
            csv_df = pd.read_csv(str(ENGAGEMENT_DATA_PATH))
            return csv_df[csv_df["store_id"] == store_id][
                ["sku_id", "impression_count", "pick_count", "conversion_rate"]
            ].reset_index(drop=True)

        return pd.DataFrame(columns=["sku_id", "impression_count", "pick_count", "conversion_rate"])


# ═══════════════════════════════════════════════════════════════
#  Stage 2: Feature Engineering
# ═══════════════════════════════════════════════════════════════

class FeatureEngineer:
    """Computes per-SKU metrics and composite scores."""

    def compute_metrics(
        self,
        sales_df: pd.DataFrame,
        engagement_df: pd.DataFrame,
    ) -> list[SKUMetrics]:
        """
        Calculate velocity, profit, engagement, and composite score per SKU.
        """
        if sales_df.empty:
            return []

        # Merge engagement into sales
        merged = sales_df.copy()
        if not engagement_df.empty:
            merged = merged.merge(
                engagement_df, on="sku_id", how="left", suffixes=("", "_eng")
            )
        for col in ["impression_count", "pick_count", "conversion_rate"]:
            if col not in merged.columns:
                merged[col] = 0

        merged["impression_count"] = merged["impression_count"].fillna(0).astype(int)
        merged["pick_count"] = merged["pick_count"].fillna(0).astype(int)
        merged["conversion_rate"] = merged["conversion_rate"].fillna(0.0)

        # Compute raw metrics
        num_weeks = max(merged["num_days"].max() / 7.0, 1.0)
        merged["sales_velocity"] = merged["total_quantity"] / num_weeks
        merged["profit_contribution"] = merged["total_quantity"] * merged["unit_price"]

        # Engagement score = blend of normalized conversion rate and impression volume
        max_impressions = max(merged["impression_count"].max(), 1)
        merged["impression_norm"] = merged["impression_count"] / max_impressions
        merged["engagement_score"] = (
            0.6 * merged["conversion_rate"]
            + 0.4 * merged["impression_norm"]
        )

        # Normalize for composite
        for col in ["sales_velocity", "profit_contribution", "engagement_score"]:
            col_max = merged[col].max()
            if col_max > 0:
                merged[f"{col}_norm"] = merged[col] / col_max
            else:
                merged[f"{col}_norm"] = 0.0

        # Composite score
        merged["composite_score"] = (
            SCORE_WEIGHT_VELOCITY * merged["sales_velocity_norm"]
            + SCORE_WEIGHT_PROFIT * merged["profit_contribution_norm"]
            + SCORE_WEIGHT_ENGAGEMENT * merged["engagement_score_norm"]
        )

        # Classify tiers
        p80 = merged["composite_score"].quantile(TOP_PERFORMER_PERCENTILE)
        p50 = merged["composite_score"].quantile(0.50)

        sku_list: list[SKUMetrics] = []
        for _, row in merged.iterrows():
            score = row["composite_score"]
            if score >= p80:
                tier = "Premium"
            elif score >= p50:
                tier = "Standard"
            else:
                tier = "Economy"

            sku_list.append(SKUMetrics(
                sku_id=row["sku_id"],
                product_name=row["product_name"],
                category=row["category"],
                unit_price=round(row["unit_price"], 2),
                total_quantity=int(row["total_quantity"]),
                total_revenue=round(row["total_revenue"], 2),
                sales_velocity=round(row["sales_velocity"], 2),
                profit_contribution=round(row["profit_contribution"], 2),
                impression_count=int(row["impression_count"]),
                pick_count=int(row["pick_count"]),
                conversion_rate=round(row["conversion_rate"], 4),
                engagement_score=round(row["engagement_score"], 4),
                composite_score=round(score, 4),
                tier=tier,
            ))

        return sku_list


# ═══════════════════════════════════════════════════════════════
#  Stage 3: Shelf Placement Optimizer (Greedy Algorithm)
# ═══════════════════════════════════════════════════════════════

class ShelfPlacementOptimizer:
    """
    Greedy placement algorithm that assigns SKUs to shelf slots.

    Rules:
      1. Top 20% (Premium) → eye-level shelves (2, 3)
      2. Bottom 30% (Economy) → bottom shelf (1) or top shelves (4, 5)
      3. SKUs are grouped by category → each category gets dedicated aisles/sections
    """

    def __init__(self, store_id: str) -> None:
        self.store_id = store_id
        config = STORE_CONFIG.get(store_id)
        if not config:
            raise ValueError(f"Store {store_id} not found in STORE_CONFIG")
        self.num_aisles: int = config["aisles"]
        self.shelves_per_aisle: int = config["shelves_per_aisle"]
        self.sections_per_shelf: int = config["sections_per_shelf"]
        self.total_slots: int = self.num_aisles * self.shelves_per_aisle * self.sections_per_shelf

    def _build_slots(self) -> list[PlacementSlot]:
        """Create all available placement slots for the store."""
        slots: list[PlacementSlot] = []
        for aisle_idx in range(self.num_aisles):
            aisle_num = aisle_idx + 1
            aisle_id = f"A{aisle_num:02d}"
            for shelf_num in range(1, self.shelves_per_aisle + 1):
                shelf_id = f"{aisle_id}-S{shelf_num:02d}"
                for sec_num in range(1, self.sections_per_shelf + 1):
                    section_id = f"{shelf_id}-P{sec_num:02d}"
                    slots.append(PlacementSlot(
                        aisle_idx=aisle_idx,
                        shelf_number=shelf_num,
                        section_number=sec_num,
                        aisle_id=aisle_id,
                        shelf_id=shelf_id,
                        section_id=section_id,
                    ))
        return slots

    def optimize(self, sku_metrics: list[SKUMetrics]) -> list[PlacementSlot]:
        """
        Run the greedy placement algorithm.

        Steps:
          1. Group SKUs by category.
          2. Allocate aisles to categories (round-robin so every category
             gets at least a share, even when aisles < categories).
          3. Within each category's aisles, fill eye-level shelves first
             with Premium, then Standard on mid-shelves, Economy on bottom/top.
          4. Global fallback: any SKUs that couldn't be placed in their
             category's aisles overflow into any remaining empty slot,
             still respecting tier → shelf priority.
        """
        if not sku_metrics:
            return []

        slots = self._build_slots()

        # ── Group SKUs by category ──
        category_skus: dict[str, list[SKUMetrics]] = {}
        for sku in sku_metrics:
            category_skus.setdefault(sku.category, []).append(sku)

        # Sort each category's SKUs by composite score descending
        for cat in category_skus:
            category_skus[cat].sort(key=lambda s: s.composite_score, reverse=True)

        # ── Allocate aisles to categories (round-robin) ──
        categories = sorted(category_skus.keys())
        aisle_allocation: dict[str, list[int]] = {c: [] for c in categories}

        for aisle_idx in range(self.num_aisles):
            cat = categories[aisle_idx % len(categories)]
            aisle_allocation[cat].append(aisle_idx)

        # ── Place SKUs into their category's aisles ──
        unplaced: list[SKUMetrics] = []

        for cat, aisle_indices in aisle_allocation.items():
            skus = category_skus.get(cat, [])
            if not skus:
                continue

            # Split SKUs into tiers
            premium = [s for s in skus if s.tier == "Premium"]
            standard = [s for s in skus if s.tier == "Standard"]
            economy = [s for s in skus if s.tier == "Economy"]

            # Gather available slots for this category's aisles
            cat_slots = [s for s in slots if s.aisle_idx in aisle_indices]

            eye_level = [s for s in cat_slots if s.shelf_number in EYE_LEVEL_SHELVES and s.assigned_sku is None]
            mid = [s for s in cat_slots if s.shelf_number not in EYE_LEVEL_SHELVES
                   and s.shelf_number != 1 and s.shelf_number < self.shelves_per_aisle
                   and s.assigned_sku is None]
            bottom_top = [s for s in cat_slots if (s.shelf_number == 1 or s.shelf_number >= self.shelves_per_aisle)
                          and s.shelf_number not in EYE_LEVEL_SHELVES
                          and s.assigned_sku is None]

            # Place Premium → eye-level first
            leftover_p = self._fill_slots(premium, eye_level + mid + bottom_top)
            # Re-check available slots after placing premium
            mid = [s for s in cat_slots if s.assigned_sku is None and s.shelf_number not in EYE_LEVEL_SHELVES
                   and s.shelf_number != 1 and s.shelf_number < self.shelves_per_aisle]
            eye_level = [s for s in cat_slots if s.assigned_sku is None and s.shelf_number in EYE_LEVEL_SHELVES]
            bottom_top = [s for s in cat_slots if s.assigned_sku is None
                          and (s.shelf_number == 1 or s.shelf_number >= self.shelves_per_aisle)
                          and s.shelf_number not in EYE_LEVEL_SHELVES]

            # Place Standard → mid first
            leftover_s = self._fill_slots(standard, mid + eye_level + bottom_top)
            # Re-check
            remaining = [s for s in cat_slots if s.assigned_sku is None]

            # Place Economy → any remaining
            leftover_e = self._fill_slots(economy, remaining)

            # Collect any that couldn't fit
            unplaced.extend(leftover_p + leftover_s + leftover_e)

        # ── Global fallback: place unplaced SKUs in ANY empty slot ──
        if unplaced:
            # Sort unplaced by composite score descending so best SKUs get priority
            unplaced.sort(key=lambda s: s.composite_score, reverse=True)
            all_empty = [s for s in slots if s.assigned_sku is None]

            # Separate by tier for best-effort shelf matching
            up_premium = [s for s in unplaced if s.tier == "Premium"]
            up_standard = [s for s in unplaced if s.tier == "Standard"]
            up_economy = [s for s in unplaced if s.tier == "Economy"]

            eye_empty = [s for s in all_empty if s.shelf_number in EYE_LEVEL_SHELVES]
            mid_empty = [s for s in all_empty if s.shelf_number not in EYE_LEVEL_SHELVES
                         and s.shelf_number != 1 and s.shelf_number < self.shelves_per_aisle]
            bt_empty = [s for s in all_empty if (s.shelf_number == 1 or s.shelf_number >= self.shelves_per_aisle)
                        and s.shelf_number not in EYE_LEVEL_SHELVES]

            self._fill_slots(up_premium, eye_empty + mid_empty + bt_empty)
            mid_empty = [s for s in all_empty if s.assigned_sku is None and s.shelf_number not in EYE_LEVEL_SHELVES
                         and s.shelf_number != 1 and s.shelf_number < self.shelves_per_aisle]
            eye_empty = [s for s in all_empty if s.assigned_sku is None and s.shelf_number in EYE_LEVEL_SHELVES]
            bt_empty = [s for s in all_empty if s.assigned_sku is None
                        and (s.shelf_number == 1 or s.shelf_number >= self.shelves_per_aisle)
                        and s.shelf_number not in EYE_LEVEL_SHELVES]
            self._fill_slots(up_standard, mid_empty + eye_empty + bt_empty)
            final_empty = [s for s in all_empty if s.assigned_sku is None]
            self._fill_slots(up_economy, final_empty)

        return slots

    @staticmethod
    def _fill_slots(skus: list[SKUMetrics], slot_priority: list[PlacementSlot]) -> list[SKUMetrics]:
        """
        Assign SKUs to the first available slot in priority order.
        Returns any SKUs that couldn't be placed (no available slots).
        """
        leftover: list[SKUMetrics] = []
        sku_iter = iter(skus)
        current_sku = next(sku_iter, None)
        for slot in slot_priority:
            if current_sku is None:
                break
            if slot.assigned_sku is None:
                slot.assigned_sku = current_sku
                current_sku = next(sku_iter, None)
        # Collect remaining unplaced
        if current_sku is not None:
            leftover.append(current_sku)
        leftover.extend(sku_iter)
        return leftover


# ═══════════════════════════════════════════════════════════════
#  Stage 4: Planogram Builder
# ═══════════════════════════════════════════════════════════════

class PlanogramBuilder:
    """Converts placement slots into a fully compliant Planogram Pydantic object."""

    def build(self, store_id: str, slots: list[PlacementSlot]) -> Planogram:
        """Build a Planogram from optimized placement slots."""
        config = STORE_CONFIG.get(store_id)
        if not config:
            raise ValueError(f"Store {store_id} not found in STORE_CONFIG")

        store_name = config["name"]

        # Organize slots into aisle → shelf → sections hierarchy
        aisle_map: dict[str, dict[str, list[PlacementSlot]]] = {}
        for slot in slots:
            aisle_map.setdefault(slot.aisle_id, {}).setdefault(slot.shelf_id, []).append(slot)

        aisles: list[Aisle] = []
        for aisle_id in sorted(aisle_map.keys()):
            shelf_map = aisle_map[aisle_id]
            shelves: list[ShelfSection] = []
            for shelf_id in sorted(shelf_map.keys()):
                slot_list = sorted(shelf_map[shelf_id], key=lambda s: s.section_number)
                sections: list[ProductFacing] = []
                for slot in slot_list:
                    if slot.assigned_sku is not None:
                        sku = slot.assigned_sku
                        sections.append(ProductFacing(
                            position=slot.section_number,
                            section_id=slot.section_id,
                            sku_id=sku.sku_id,
                            product_name=sku.product_name,
                            expected_facings=3,
                            price=sku.unit_price,
                            min_stock=3,
                        ))
                    else:
                        # Empty slot placeholder
                        sections.append(ProductFacing(
                            position=slot.section_number,
                            section_id=slot.section_id,
                            sku_id="EMPTY",
                            product_name="(vacant)",
                            expected_facings=0,
                            price=0.0,
                            min_stock=0,
                        ))

                # Extract shelf number from shelf_id (e.g., "A01-S02" → 2)
                shelf_num = int(shelf_id.split("-S")[1])
                shelves.append(ShelfSection(
                    shelf_id=shelf_id,
                    shelf_number=shelf_num,
                    sections=sections,
                ))

            aisle_num = int(aisle_id.replace("A", ""))
            aisles.append(Aisle(
                aisle_id=aisle_id,
                aisle_name=f"Aisle {aisle_num}",
                shelves=shelves,
            ))

        return Planogram(
            store_id=store_id,
            store_name=store_name,
            generated_at=datetime.now().isoformat(),
            aisles=aisles,
        )

    def save_planogram(self, planogram: Planogram, output_dir: Path = OPTIMIZER_OUTPUT_DIR) -> Path:
        """Save planogram as JSON file."""
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"optimized_planogram_{planogram.store_id.lower()}.json"
        with open(path, "w") as f:
            json.dump(planogram.model_dump(), f, indent=2)
        return path


# ═══════════════════════════════════════════════════════════════
#  Convenience: Run full optimization for a store
# ═══════════════════════════════════════════════════════════════

def optimize_store(store_id: str, db_path: Path = DATABASE_PATH) -> tuple[Planogram, list[SKUMetrics]]:
    """
    Run the full optimization pipeline for a single store.

    Returns:
        (optimized_planogram, sku_metrics)
    """
    ingestor = DataIngestor(db_path)
    engineer = FeatureEngineer()
    optimizer = ShelfPlacementOptimizer(store_id)
    builder = PlanogramBuilder()

    # Ingest
    sales_df = ingestor.get_sales_summary(store_id)
    engagement_df = ingestor.get_engagement_data(store_id)

    # Feature engineering
    sku_metrics = engineer.compute_metrics(sales_df, engagement_df)

    # Optimize placement
    slots = optimizer.optimize(sku_metrics)

    # Build planogram
    planogram = builder.build(store_id, slots)

    return planogram, sku_metrics
