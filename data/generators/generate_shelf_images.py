"""
Generate synthetic shelf images by creating colored product blocks on shelf backgrounds.
Simulates varying stock levels, misplaced products, and empty sections.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from config.settings import SAMPLE_IMAGES_DIR

np.random.seed(42)

# Product color palette (simulates different product packaging)
PRODUCT_COLORS = [
    (220, 50, 50),    # Red (Coca-Cola)
    (50, 100, 220),   # Blue (Pepsi)
    (50, 180, 50),    # Green (Sprite)
    (255, 165, 0),    # Orange (Juice)
    (100, 200, 255),  # Light Blue (Water)
    (255, 215, 0),    # Gold (Chips)
    (180, 50, 180),   # Purple (Doritos)
    (255, 100, 100),  # Light Red (Pringles)
    (60, 60, 60),     # Dark (Oreo)
    (200, 50, 50),    # Red (KitKat)
    (240, 240, 240),  # White (Milk)
    (200, 200, 150),  # Cream (Yogurt)
    (255, 200, 50),   # Yellow (Cheese)
    (255, 230, 150),  # Light Yellow (Butter)
    (180, 220, 180),  # Light Green (Cream Cheese)
]

SHELF_SCENARIOS = [
    {"name": "full_shelf", "fill_rate": 0.95, "misplaced": 0},
    {"name": "low_stock_shelf", "fill_rate": 0.4, "misplaced": 0},
    {"name": "empty_sections", "fill_rate": 0.15, "misplaced": 0},
    {"name": "misplaced_products", "fill_rate": 0.8, "misplaced": 3},
    {"name": "mixed_stock", "fill_rate": 0.6, "misplaced": 1},
]


def draw_product_block(draw, x, y, w, h, color, label=""):
    """Draw a single product block with slight 3D effect."""
    # Main body
    draw.rectangle([x, y, x + w, y + h], fill=color, outline=(40, 40, 40), width=1)
    # Highlight strip (simulates label)
    label_h = max(h // 5, 4)
    lighter = tuple(min(c + 60, 255) for c in color)
    draw.rectangle([x + 2, y + h // 3, x + w - 2, y + h // 3 + label_h], fill=lighter)
    # Top highlight for 3D effect
    top_light = tuple(min(c + 30, 255) for c in color)
    draw.rectangle([x, y, x + w, y + 3], fill=top_light)


def generate_shelf_image(
    width=800,
    height=600,
    num_shelves=4,
    sections_per_shelf=6,
    fill_rate=0.9,
    misplaced=0,
    scenario_name="default",
):
    """Generate a synthetic shelf image."""
    # Background (store wall)
    img = Image.new("RGB", (width, height), (235, 230, 220))
    draw = ImageDraw.Draw(img)

    shelf_height = height // (num_shelves + 1)
    product_margin = 4
    annotations = []

    for shelf_idx in range(num_shelves):
        shelf_y = 40 + shelf_idx * shelf_height
        shelf_bottom = shelf_y + shelf_height - 15

        # Draw shelf board
        draw.rectangle(
            [20, shelf_bottom, width - 20, shelf_bottom + 10],
            fill=(139, 90, 43),
            outline=(100, 65, 30),
            width=2,
        )
        # Shelf shadow
        draw.rectangle(
            [22, shelf_bottom + 10, width - 22, shelf_bottom + 14],
            fill=(100, 65, 30),
        )

        section_width = (width - 60) // sections_per_shelf
        product_h = shelf_height - 30

        for sec_idx in range(sections_per_shelf):
            sec_x = 30 + sec_idx * section_width
            color_idx = (shelf_idx * sections_per_shelf + sec_idx) % len(PRODUCT_COLORS)
            color = PRODUCT_COLORS[color_idx]

            # Determine how many products (facings) in this section
            max_facings = max(section_width // 25, 2)
            if np.random.random() < fill_rate:
                # Section has products
                num_products = np.random.randint(max(1, int(max_facings * 0.5)), max_facings + 1)

                # Check if this section should have a misplaced product
                if misplaced > 0 and np.random.random() < 0.15:
                    # Use a wrong color (misplaced product)
                    wrong_idx = (color_idx + np.random.randint(3, 8)) % len(PRODUCT_COLORS)
                    color = PRODUCT_COLORS[wrong_idx]
                    misplaced -= 1

                prod_w = (section_width - product_margin * 2) // max(num_products, 1) - 2
                prod_w = max(prod_w, 15)

                for p in range(num_products):
                    px = sec_x + product_margin + p * (prod_w + 2)
                    py = shelf_bottom - product_h
                    # Slight height variation
                    h_var = np.random.randint(-8, 5)
                    actual_h = product_h + h_var

                    draw_product_block(draw, px, shelf_bottom - actual_h, prod_w, actual_h, color)

                    annotations.append({
                        "shelf": shelf_idx,
                        "section": sec_idx,
                        "product_idx": p,
                        "bbox": [px, shelf_bottom - actual_h, prod_w, actual_h],
                        "stock_level": "FULL" if num_products >= max_facings * 0.7 else "LOW",
                    })

                # Price tag
                tag_y = shelf_bottom + 12
                tag_x = sec_x + section_width // 2 - 15
                draw.rectangle([tag_x, tag_y, tag_x + 30, tag_y + 10], fill=(255, 255, 255), outline=(0, 0, 0))
                try:
                    draw.text((tag_x + 3, tag_y + 1), f"${np.random.uniform(1, 7):.2f}", fill=(0, 0, 0))
                except Exception:
                    pass
            else:
                # Empty section — draw empty shelf area
                annotations.append({
                    "shelf": shelf_idx,
                    "section": sec_idx,
                    "product_idx": -1,
                    "bbox": [sec_x, shelf_bottom - product_h, section_width - 10, product_h],
                    "stock_level": "EMPTY",
                })

    return img, annotations


def generate_all_shelf_images():
    """Generate shelf images for all scenarios."""
    print("Generating synthetic shelf images...")
    SAMPLE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    all_annotations = {}
    for scenario in SHELF_SCENARIOS:
        img, annotations = generate_shelf_image(
            fill_rate=scenario["fill_rate"],
            misplaced=scenario["misplaced"],
            scenario_name=scenario["name"],
        )
        filename = f"shelf_{scenario['name']}.png"
        img_path = SAMPLE_IMAGES_DIR / filename
        img.save(img_path, "PNG")
        all_annotations[scenario["name"]] = annotations
        print(f"  ✓ {filename}: {len(annotations)} product regions, fill_rate={scenario['fill_rate']}")

    # Generate per-store images (3 per store, different stock levels)
    for store_num in range(1, 4):
        for i, fill in enumerate([0.9, 0.5, 0.2]):
            img, ann = generate_shelf_image(
                fill_rate=fill,
                misplaced=1 if fill > 0.4 else 0,
                scenario_name=f"store{store_num:02d}_cam{i+1}",
            )
            filename = f"store{store_num:02d}_camera{i+1}.png"
            img_path = SAMPLE_IMAGES_DIR / filename
            img.save(img_path, "PNG")
            print(f"  ✓ {filename}: fill={fill}")

    print(f"  ✓ All images saved to {SAMPLE_IMAGES_DIR}")
    return all_annotations


if __name__ == "__main__":
    generate_all_shelf_images()
