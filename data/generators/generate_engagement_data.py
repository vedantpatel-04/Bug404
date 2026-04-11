"""
Synthetic customer engagement data generator.
Simulates 'views vs picks' behavior per SKU per store by reading actual POS
sales data and inferring impression counts based on shelf-visibility heuristics.

This ensures consistency: pick_count ≈ total units sold from POS,
while impression_count is derived via a visibility multiplier + noise.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import numpy as np
from typing import Optional

from config.settings import (
    POS_DATA_DIR,
    CATEGORIES,
    NUM_STORES,
    SHELF_VISIBILITY_MULTIPLIER,
)

np.random.seed(42)

# Category-level base conversion rates (some categories naturally convert better)
CATEGORY_BASE_CONVERSION: dict[str, float] = {
    "Beverages": 0.18,
    "Snacks": 0.22,
    "Dairy": 0.15,
    "Bakery": 0.14,
    "Canned Goods": 0.10,
    "Frozen Foods": 0.12,
    "Personal Care": 0.08,
    "Household": 0.07,
    "Condiments": 0.11,
    "Cereals": 0.13,
}


def load_pos_transactions() -> pd.DataFrame:
    """Load POS transaction data to derive pick counts."""
    path = POS_DATA_DIR / "pos_transactions.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"POS data not found at {path}. Run generate_pos_data.py first."
        )
    return pd.read_csv(path)


def generate_engagement_data(pos_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """
    Generate customer engagement data from POS transactions.

    For each (store_id, sku_id) pair:
      - pick_count   = total quantity_sold across all dates
      - impression_count = pick_count / simulated_conversion_rate
      - conversion_rate  = pick_count / impression_count

    The simulated conversion rate is based on:
      1. Category base rate
      2. A random shelf-position visibility factor (simulating current random layout)
      3. Gaussian noise for realism
    """
    if pos_df is None:
        pos_df = load_pos_transactions()

    # Aggregate total picks per store × SKU
    picks = (
        pos_df.groupby(["store_id", "sku_id", "category"])["quantity_sold"]
        .sum()
        .reset_index()
        .rename(columns={"quantity_sold": "pick_count"})
    )

    records: list[dict] = []
    for _, row in picks.iterrows():
        store_id: str = row["store_id"]
        sku_id: str = row["sku_id"]
        category: str = row["category"]
        pick_count: int = int(row["pick_count"])

        # Base conversion for this category
        base_conv = CATEGORY_BASE_CONVERSION.get(category, 0.12)

        # Simulate a random "current shelf position" (before optimization)
        random_shelf = np.random.randint(1, 6)  # shelves 1-5
        visibility = SHELF_VISIBILITY_MULTIPLIER.get(random_shelf, 1.0)

        # Adjusted conversion = base * visibility factor * noise
        noise = np.random.normal(1.0, 0.10)
        noise = max(noise, 0.5)
        simulated_conv = min(base_conv * visibility * noise, 0.95)
        simulated_conv = max(simulated_conv, 0.02)

        # Derive impressions from picks
        impression_count = int(pick_count / simulated_conv) if simulated_conv > 0 else pick_count * 10
        impression_count = max(impression_count, pick_count)  # can't have fewer impressions than picks

        # Final conversion rate
        conversion_rate = round(pick_count / impression_count, 4) if impression_count > 0 else 0.0

        records.append({
            "store_id": store_id,
            "sku_id": sku_id,
            "category": category,
            "impression_count": impression_count,
            "pick_count": pick_count,
            "conversion_rate": conversion_rate,
        })

    return pd.DataFrame(records)


def save_engagement_data(pos_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Generate and save engagement data to CSV."""
    print("Generating customer engagement data...")
    df = generate_engagement_data(pos_df)
    output_path = POS_DATA_DIR / "customer_engagement.csv"
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved {len(df):,} engagement records to {output_path}")
    print(f"    Avg conversion rate: {df['conversion_rate'].mean():.2%}")
    print(f"    Total impressions:   {df['impression_count'].sum():,}")
    print(f"    Total picks:         {df['pick_count'].sum():,}")
    return df


if __name__ == "__main__":
    save_engagement_data()
