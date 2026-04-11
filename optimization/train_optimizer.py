"""
Training & Evaluation Script for the AI Shelf Arrangement Optimizer.

End-to-end pipeline that:
  1. Generates 2 years of synthetic POS + engagement data
  2. Seeds the SQLite database
  3. Runs the shelf optimization algorithm for each store
  4. Prints a 'Before vs After' revenue lift comparison
  5. Saves optimized planograms as JSON
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime

from config.settings import (
    DATABASE_PATH,
    STORE_CONFIG,
    POS_DATA_DIR,
    OPTIMIZER_OUTPUT_DIR,
    SHELF_VISIBILITY_MULTIPLIER,
    EYE_LEVEL_SHELVES,
)
from database.models import create_tables
from data.generators.generate_pos_data import save_pos_data, generate_product_catalog
from data.generators.generate_engagement_data import save_engagement_data
from optimization.shelf_optimizer import (
    optimize_store,
    DataIngestor,
    SKUMetrics,
    PlanogramBuilder,
)
from planogram.schemas import Planogram


# ─── ANSI Colors for Terminal Output ─────────────────────────
class C:
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    DIM = "\033[2m"
    RESET = "\033[0m"
    UNDERLINE = "\033[4m"


def banner(text: str) -> None:
    width = 64
    print(f"\n{C.CYAN}{'═' * width}")
    print(f"  {C.BOLD}{text}{C.RESET}{C.CYAN}")
    print(f"{'═' * width}{C.RESET}\n")


# ═══════════════════════════════════════════════════════════════
#  Step 1: Generate Synthetic Data
# ═══════════════════════════════════════════════════════════════

def step_generate_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate POS transactions + engagement data."""
    banner("STEP 1: Generating Synthetic Data (2 Years)")
    pos_df, catalog = save_pos_data()
    engagement_df = save_engagement_data(pos_df)
    return pos_df, catalog, engagement_df


# ═══════════════════════════════════════════════════════════════
#  Step 2: Seed Database
# ═══════════════════════════════════════════════════════════════

def step_seed_database(
    pos_df: pd.DataFrame,
    catalog: pd.DataFrame,
    engagement_df: pd.DataFrame,
) -> None:
    """Create tables and load data into SQLite."""
    banner("STEP 2: Seeding Database")

    # Recreate the database
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()
    create_tables(DATABASE_PATH)

    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()

    # ── Insert stores ──
    for store_id, config in STORE_CONFIG.items():
        cursor.execute(
            "INSERT OR REPLACE INTO stores (store_id, store_name, num_aisles, shelves_per_aisle, sections_per_shelf) VALUES (?, ?, ?, ?, ?)",
            (store_id, config["name"], config["aisles"], config["shelves_per_aisle"], config["sections_per_shelf"]),
        )
    print(f"  ✓ Inserted {len(STORE_CONFIG)} stores")

    # ── Insert products ──
    for _, row in catalog.iterrows():
        cursor.execute(
            "INSERT OR REPLACE INTO products (sku_id, product_name, category, unit_price, max_stock) VALUES (?, ?, ?, ?, ?)",
            (row["sku_id"], row["product_name"], row["category"], row["unit_price"], int(row["max_stock"])),
        )
    print(f"  ✓ Inserted {len(catalog)} products")

    # ── Insert POS transactions ──
    pos_df.to_sql("pos_transactions", conn, if_exists="append", index=False)
    print(f"  ✓ Inserted {len(pos_df):,} POS transactions")

    # ── Insert engagement data ──
    engagement_df.to_sql("customer_engagement", conn, if_exists="append", index=False)
    print(f"  ✓ Inserted {len(engagement_df):,} engagement records")

    conn.commit()
    conn.close()
    print(f"  ✓ Database ready at {DATABASE_PATH}")


# ═══════════════════════════════════════════════════════════════
#  Step 3: Run Optimization
# ═══════════════════════════════════════════════════════════════

def step_run_optimization() -> dict[str, tuple[Planogram, list[SKUMetrics]]]:
    """Run the optimizer for each store."""
    banner("STEP 3: Running Shelf Optimization")
    results: dict[str, tuple[Planogram, list[SKUMetrics]]] = {}

    for store_id in STORE_CONFIG:
        print(f"\n  {C.YELLOW}▶ Optimizing {store_id} ({STORE_CONFIG[store_id]['name']}){C.RESET}")
        planogram, sku_metrics = optimize_store(store_id)

        # Save planogram
        builder = PlanogramBuilder()
        path = builder.save_planogram(planogram)

        # Validate using Pydantic
        validated = Planogram.model_validate(planogram.model_dump())
        total_sections = validated.total_sections()
        filled = sum(1 for s in validated.get_all_sections() if s.sku_id != "EMPTY")

        # Tier summary
        tier_counts = {"Premium": 0, "Standard": 0, "Economy": 0}
        for m in sku_metrics:
            tier_counts[m.tier] = tier_counts.get(m.tier, 0) + 1

        print(f"    ✓ {len(planogram.aisles)} aisles, {total_sections} sections ({filled} filled)")
        print(f"    ✓ Tiers: {C.GREEN}Premium={tier_counts['Premium']}{C.RESET}, "
              f"Standard={tier_counts['Standard']}, "
              f"{C.DIM}Economy={tier_counts['Economy']}{C.RESET}")
        print(f"    ✓ Saved → {path}")

        results[store_id] = (planogram, sku_metrics)

    return results


# ═══════════════════════════════════════════════════════════════
#  Step 4: Before vs After Comparison
# ═══════════════════════════════════════════════════════════════

def _get_sku_shelf_positions(planogram: Planogram) -> dict[str, int]:
    """Build a map of sku_id → shelf_number from the planogram."""
    sku_shelf: dict[str, int] = {}
    for aisle in planogram.aisles:
        for shelf in aisle.shelves:
            for sec in shelf.sections:
                if sec.sku_id != "EMPTY" and sec.sku_id not in sku_shelf:
                    sku_shelf[sec.sku_id] = shelf.shelf_number
    return sku_shelf


def estimate_weekly_revenue(
    sku_metrics: list[SKUMetrics],
    planogram: Planogram,
    is_optimized: bool,
) -> float:
    """
    Estimate weekly revenue for a planogram layout.

    Both baseline and optimized are computed over ALL SKUs so the
    comparison is apples-to-apples:
      - Baseline:   each SKU gets the average visibility (random placement)
      - Optimized:  placed SKUs get their actual shelf visibility;
                    unplaced SKUs keep the average visibility.
    """
    avg_vis = float(np.mean(list(SHELF_VISIBILITY_MULTIPLIER.values())))
    sku_shelf = _get_sku_shelf_positions(planogram)
    sku_map = {m.sku_id: m for m in sku_metrics}

    total = 0.0
    for m in sku_metrics:
        base_rev = m.sales_velocity * m.unit_price
        if is_optimized and m.sku_id in sku_shelf:
            vis = SHELF_VISIBILITY_MULTIPLIER.get(sku_shelf[m.sku_id], 1.0)
        else:
            vis = avg_vis
        total += base_rev * vis

    return round(total, 2)


def step_before_after_comparison(
    results: dict[str, tuple[Planogram, list[SKUMetrics]]],
) -> None:
    """Print before vs after revenue comparison."""
    banner("STEP 4: Before vs After Revenue Comparison")

    # Header
    print(f"  {C.BOLD}{'Store':<35} {'Baseline ($/wk)':>15} {'Optimized ($/wk)':>17} {'Lift':>10} {'Lift %':>9}{C.RESET}")
    print(f"  {'─' * 90}")

    total_baseline = 0.0
    total_optimized = 0.0

    for store_id, (planogram, sku_metrics) in results.items():
        store_name = STORE_CONFIG[store_id]["name"]

        baseline_rev = estimate_weekly_revenue(sku_metrics, planogram, is_optimized=False)
        optimized_rev = estimate_weekly_revenue(sku_metrics, planogram, is_optimized=True)
        lift = optimized_rev - baseline_rev
        lift_pct = (lift / baseline_rev * 100) if baseline_rev > 0 else 0.0

        total_baseline += baseline_rev
        total_optimized += optimized_rev

        color = C.GREEN if lift > 0 else C.RED
        print(
            f"  {store_name:<35} "
            f"${baseline_rev:>13,.2f} "
            f"${optimized_rev:>15,.2f} "
            f"{color}${lift:>+9,.2f}{C.RESET} "
            f"{color}{lift_pct:>+8.1f}%{C.RESET}"
        )

    # Totals
    total_lift = total_optimized - total_baseline
    total_pct = (total_lift / total_baseline * 100) if total_baseline > 0 else 0.0
    print(f"  {'─' * 90}")
    color = C.GREEN if total_lift > 0 else C.RED
    print(
        f"  {C.BOLD}{'TOTAL':<35}{C.RESET} "
        f"${total_baseline:>13,.2f} "
        f"${total_optimized:>15,.2f} "
        f"{color}{C.BOLD}${total_lift:>+9,.2f}{C.RESET} "
        f"{color}{C.BOLD}{total_pct:>+8.1f}%{C.RESET}"
    )

    # Eye-level placement verification
    print(f"\n{C.CYAN}  ── Eye-Level Placement Verification ──{C.RESET}")
    for store_id, (planogram, sku_metrics) in results.items():
        premium_skus = {m.sku_id for m in sku_metrics if m.tier == "Premium"}
        eye_level_skus: set[str] = set()
        for aisle in planogram.aisles:
            for shelf in aisle.shelves:
                if shelf.shelf_number in EYE_LEVEL_SHELVES:
                    for sec in shelf.sections:
                        if sec.sku_id != "EMPTY":
                            eye_level_skus.add(sec.sku_id)

        premium_at_eye = premium_skus & eye_level_skus
        pct = len(premium_at_eye) / len(premium_skus) * 100 if premium_skus else 0
        status = f"{C.GREEN}✓{C.RESET}" if pct >= 70 else f"{C.YELLOW}⚠{C.RESET}"
        print(f"  {status} {store_id}: {len(premium_at_eye)}/{len(premium_skus)} premium SKUs at eye level ({pct:.0f}%)")


# ═══════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════

def main() -> None:
    """Run the complete training & evaluation pipeline."""
    start = datetime.now()
    print(f"\n{C.BOLD}{'[*] AI Shelf Arrangement Optimizer':^64}{C.RESET}")
    print(f"{C.DIM}{'Training & Evaluation Pipeline':^64}{C.RESET}")

    # Step 1: Generate data
    pos_df, catalog, engagement_df = step_generate_data()

    # Step 2: Seed database
    step_seed_database(pos_df, catalog, engagement_df)

    # Step 3: Optimize
    results = step_run_optimization()

    # Step 4: Compare
    step_before_after_comparison(results)

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{C.DIM}  Pipeline completed in {elapsed:.1f}s{C.RESET}")
    print(f"  Optimized planograms saved to: {OPTIMIZER_OUTPUT_DIR}\n")


if __name__ == "__main__":
    main()
