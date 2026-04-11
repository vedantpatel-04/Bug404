"""
Generate sample planogram JSON definitions for each store.
Defines expected shelf layout: which SKU goes where, expected facings, and pricing.
"""
import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
from config.settings import STORE_CONFIG, PLANOGRAM_DIR, NUM_SKUS

np.random.seed(42)


def generate_planograms():
    """Generate planogram JSON files for all stores."""
    print("Generating planogram definitions...")
    sku_list = [f"SKU{i+1:03d}" for i in range(NUM_SKUS)]
    product_names = [
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
    prices = [
        1.99, 1.89, 1.49, 3.49, 1.29, 3.49, 3.99, 4.29, 2.99, 1.49,
        2.49, 4.99, 3.99, 3.49, 2.99, 2.29, 2.79, 3.99, 3.49, 4.49,
        2.49, 1.79, 1.99, 1.69, 1.89, 5.99, 4.99, 3.49, 4.99, 5.49,
        5.99, 2.99, 2.49, 3.99, 2.99, 2.99, 6.99, 3.49, 4.99, 1.99,
        2.49, 1.99, 2.99, 3.49, 6.99, 3.99, 4.49, 2.99, 3.49, 4.99,
    ]

    for store_id, config in STORE_CONFIG.items():
        planogram = {
            "store_id": store_id,
            "store_name": config["name"],
            "generated_at": "2026-04-01T00:00:00",
            "aisles": []
        }

        sku_idx = 0
        for aisle_num in range(1, config["aisles"] + 1):
            aisle = {
                "aisle_id": f"A{aisle_num:02d}",
                "aisle_name": f"Aisle {aisle_num}",
                "shelves": []
            }

            for shelf_num in range(1, config["shelves_per_aisle"] + 1):
                shelf = {
                    "shelf_id": f"A{aisle_num:02d}-S{shelf_num:02d}",
                    "shelf_number": shelf_num,
                    "sections": []
                }

                for section_num in range(1, config["sections_per_shelf"] + 1):
                    sku = sku_list[sku_idx % len(sku_list)]
                    section = {
                        "position": section_num,
                        "section_id": f"A{aisle_num:02d}-S{shelf_num:02d}-P{section_num:02d}",
                        "sku_id": sku,
                        "product_name": product_names[sku_idx % len(product_names)],
                        "expected_facings": int(np.random.choice([2, 3, 4, 5], p=[0.1, 0.4, 0.3, 0.2])),
                        "price": prices[sku_idx % len(prices)],
                        "min_stock": int(np.random.randint(3, 8)),
                    }
                    shelf["sections"].append(section)
                    sku_idx += 1

                aisle["shelves"].append(shelf)
            planogram["aisles"].append(aisle)

        # Save planogram JSON
        output_path = PLANOGRAM_DIR / f"planogram_{store_id.lower()}.json"
        with open(output_path, "w") as f:
            json.dump(planogram, f, indent=2)
        total_sections = sum(
            len(s["sections"])
            for a in planogram["aisles"]
            for s in a["shelves"]
        )
        print(f"  ✓ {store_id}: {len(planogram['aisles'])} aisles, {total_sections} sections → {output_path}")

    return planogram


if __name__ == "__main__":
    generate_planograms()
