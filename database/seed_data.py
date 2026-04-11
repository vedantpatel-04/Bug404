"""
Database seeding script — runs all data generators and loads data into SQLite.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from config.settings import DATABASE_PATH, STORE_CONFIG, POS_DATA_DIR
from database.db_manager import DatabaseManager
from data.generators.generate_pos_data import save_pos_data, generate_product_catalog
from data.generators.generate_planograms import generate_planograms
from data.generators.generate_shelf_images import generate_all_shelf_images
from data.generators.generate_weather_data import generate_weather_data


def seed_database():
    """Run all generators and seed the database."""
    print("=" * 60)
    print("  SEEDING DATABASE — Smart Retail Shelf Intelligence")
    print("=" * 60)

    db = DatabaseManager()

    # 1. Generate and load product catalog
    print("\n[1/6] Product Catalog")
    catalog = generate_product_catalog()
    for _, row in catalog.iterrows():
        try:
            db.insert("products", {
                "sku_id": row["sku_id"],
                "product_name": row["product_name"],
                "category": row["category"],
                "unit_price": row["unit_price"],
                "shelf_life_days": int(row["shelf_life_days"]),
                "max_stock": int(row["max_stock"]),
                "current_stock": int(row["max_stock"] * 0.6),
            })
        except Exception:
            pass  # Already exists
    print(f"  ✓ {len(catalog)} products loaded")

    # 2. Load store definitions
    print("\n[2/6] Store Definitions")
    for store_id, config in STORE_CONFIG.items():
        try:
            db.insert("stores", {
                "store_id": store_id,
                "store_name": config["name"],
                "num_aisles": config["aisles"],
                "shelves_per_aisle": config["shelves_per_aisle"],
                "sections_per_shelf": config["sections_per_shelf"],
            })
        except Exception:
            pass
    print(f"  ✓ {len(STORE_CONFIG)} stores loaded")

    # 3. Generate shelf assignments
    print("\n[3/6] Shelf Assignments")
    sku_list = [f"SKU{i+1:03d}" for i in range(len(catalog))]
    sku_idx = 0
    shelf_count = 0
    for store_id, config in STORE_CONFIG.items():
        for aisle in range(1, config["aisles"] + 1):
            for shelf in range(1, config["shelves_per_aisle"] + 1):
                for section in range(1, config["sections_per_shelf"] + 1):
                    shelf_id = f"{store_id}-A{aisle:02d}-S{shelf:02d}-P{section:02d}"
                    try:
                        db.insert("shelves", {
                            "shelf_id": shelf_id,
                            "store_id": store_id,
                            "aisle_id": f"A{aisle:02d}",
                            "shelf_number": shelf,
                            "section_number": section,
                            "assigned_sku": sku_list[sku_idx % len(sku_list)],
                            "expected_facings": 3,
                        })
                        shelf_count += 1
                    except Exception:
                        pass
                    sku_idx += 1
    print(f"  ✓ {shelf_count} shelf sections created")

    # 4. Generate POS data
    print("\n[4/6] POS Transaction Data")
    pos_df, _ = save_pos_data()

    # Load POS data into database (batch insert for speed)
    batch_size = 5000
    pos_records = pos_df.to_dict("records")
    for i in range(0, len(pos_records), batch_size):
        batch = pos_records[i:i + batch_size]
        db.insert_many("pos_transactions", batch)
    print(f"  ✓ {len(pos_records):,} POS records loaded into database")

    # 5. Generate weather data
    print("\n[5/6] Weather & Event Data")
    weather_df = generate_weather_data()
    weather_records = weather_df.to_dict("records")
    for i in range(0, len(weather_records), batch_size):
        batch = weather_records[i:i + batch_size]
        db.insert_many("weather_data", batch)
    print(f"  ✓ {len(weather_records):,} weather records loaded")

    # 6. Generate planograms & shelf images
    print("\n[6/6] Planograms & Shelf Images")
    generate_planograms()
    generate_all_shelf_images()

    print("\n" + "=" * 60)
    print("  ✓ DATABASE SEEDING COMPLETE")
    print(f"  Database: {DATABASE_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    seed_database()
