"""
Synthetic POS transaction data generator.
Generates 2 years of daily sales data for 50 SKUs across 3 stores
with seasonal patterns, promotions, and weather-correlated demand.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.settings import NUM_SKUS, NUM_STORES, POS_HISTORY_DAYS, CATEGORIES, POS_DATA_DIR

np.random.seed(42)

# ─── Product Catalog ──────────────────────────────────────────
PRODUCT_NAMES = [
    "Coca-Cola 500ml", "Pepsi 500ml", "Sprite 330ml", "Orange Juice 1L", "Mineral Water 1.5L",
    "Lay's Classic Chips", "Doritos Nacho", "Pringles Original", "Oreo Cookies", "KitKat Bar",
    "Whole Milk 1L", "Greek Yogurt 500g", "Cheddar Cheese 200g", "Butter 250g", "Cream Cheese 150g",
    "White Bread Loaf", "Whole Wheat Bread", "Croissants 4-pack", "Bagels 6-pack", "Muffins 4-pack",
    "Tuna Canned 185g", "Baked Beans 400g", "Tomato Soup 400g", "Corn Canned 340g", "Chickpeas 400g",
    "Frozen Pizza Margherita", "Ice Cream Vanilla 1L", "Frozen Veggies Mix", "Fish Fingers 10-pack", "Frozen Berries 500g",
    "Shampoo 400ml", "Toothpaste 100g", "Hand Soap 250ml", "Deodorant Spray", "Tissue Box 100ct",
    "Dish Soap 500ml", "Laundry Detergent 1L", "Trash Bags 30ct", "Paper Towels 2-roll", "Sponges 5-pack",
    "Ketchup 500ml", "Mustard 250ml", "Soy Sauce 250ml", "Hot Sauce 150ml", "Olive Oil 500ml",
    "Corn Flakes 500g", "Granola 400g", "Oatmeal 500g", "Rice Krispies 340g", "Muesli 500g",
]

PRODUCT_PRICES = [
    1.99, 1.89, 1.49, 3.49, 1.29,
    3.49, 3.99, 4.29, 2.99, 1.49,
    2.49, 4.99, 3.99, 3.49, 2.99,
    2.29, 2.79, 3.99, 3.49, 4.49,
    2.49, 1.79, 1.99, 1.69, 1.89,
    5.99, 4.99, 3.49, 4.99, 5.49,
    5.99, 2.99, 2.49, 3.99, 2.99,
    2.99, 6.99, 3.49, 4.99, 1.99,
    2.49, 1.99, 2.99, 3.49, 6.99,
    3.99, 4.49, 2.99, 3.49, 4.99,
]


def generate_product_catalog() -> pd.DataFrame:
    """Generate the product catalog DataFrame."""
    products = []
    for i in range(NUM_SKUS):
        cat_idx = i // (NUM_SKUS // len(CATEGORIES))
        cat_idx = min(cat_idx, len(CATEGORIES) - 1)
        products.append({
            "sku_id": f"SKU{i+1:03d}",
            "product_name": PRODUCT_NAMES[i],
            "category": CATEGORIES[cat_idx],
            "unit_price": PRODUCT_PRICES[i],
            "shelf_life_days": np.random.choice([30, 90, 180, 365], p=[0.2, 0.3, 0.2, 0.3]),
            "max_stock": np.random.randint(50, 200),
        })
    return pd.DataFrame(products)


def generate_pos_data() -> pd.DataFrame:
    """Generate synthetic POS transaction data with realistic patterns."""
    catalog = generate_product_catalog()
    store_ids = [f"STORE{i+1:02d}" for i in range(NUM_STORES)]
    end_date = datetime(2026, 4, 1)
    start_date = end_date - timedelta(days=POS_HISTORY_DAYS)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    records = []
    for store_id in store_ids:
        store_multiplier = np.random.uniform(0.8, 1.3)
        for _, product in catalog.iterrows():
            # Base demand varies by category
            base_demand = np.random.uniform(5, 30)
            for date in dates:
                # Day of week effect (weekends higher)
                dow = date.dayofweek
                dow_factor = 1.3 if dow >= 5 else (0.9 if dow == 0 else 1.0)

                # Monthly seasonality
                month = date.month
                if product["category"] in ["Beverages", "Ice Cream Vanilla 1L"]:
                    season_factor = 1.0 + 0.4 * np.sin(2 * np.pi * (month - 3) / 12)  # Peak in summer
                elif product["category"] in ["Frozen Foods"]:
                    season_factor = 1.0 + 0.3 * np.sin(2 * np.pi * (month - 6) / 12)
                else:
                    season_factor = 1.0 + 0.15 * np.sin(2 * np.pi * (month - 11) / 12)  # Holiday peak

                # Holiday spikes
                holiday_factor = 1.0
                if (month == 12 and date.day >= 20) or (month == 11 and date.day >= 25):
                    holiday_factor = 1.8
                elif month == 1 and date.day <= 3:
                    holiday_factor = 1.5

                # Random promotions (~10% of days)
                promo = np.random.random() < 0.10
                promo_factor = 1.6 if promo else 1.0

                # Noise
                noise = np.random.normal(1.0, 0.15)
                noise = max(noise, 0.3)

                quantity = int(base_demand * store_multiplier * dow_factor * season_factor * holiday_factor * promo_factor * noise)
                quantity = max(0, quantity)

                if quantity > 0:
                    records.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "store_id": store_id,
                        "sku_id": product["sku_id"],
                        "product_name": product["product_name"],
                        "category": product["category"],
                        "quantity_sold": quantity,
                        "unit_price": product["unit_price"],
                        "revenue": round(quantity * product["unit_price"], 2),
                        "promotion_flag": 1 if promo else 0,
                    })

    df = pd.DataFrame(records)
    return df


def save_pos_data():
    """Generate and save POS data to CSV."""
    print("Generating POS transaction data...")
    df = generate_pos_data()
    output_path = POS_DATA_DIR / "pos_transactions.csv"
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved {len(df):,} transactions to {output_path}")

    catalog = generate_product_catalog()
    catalog_path = POS_DATA_DIR / "product_catalog.csv"
    catalog.to_csv(catalog_path, index=False)
    print(f"  ✓ Saved {len(catalog)} products to {catalog_path}")
    return df, catalog


if __name__ == "__main__":
    save_pos_data()
