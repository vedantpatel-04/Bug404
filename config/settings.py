"""
Central configuration for Smart Retail Shelf Intelligence System.
"""
import os
from pathlib import Path

# ─── Base Paths ───────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
WEIGHTS_DIR = MODELS_DIR / "weights"
SAMPLE_IMAGES_DIR = DATA_DIR / "sample_images"
PLANOGRAM_DIR = DATA_DIR / "sample_planograms"
POS_DATA_DIR = DATA_DIR / "pos_data"
DB_DIR = BASE_DIR / "database"

# Create directories
for d in [DATA_DIR, WEIGHTS_DIR, SAMPLE_IMAGES_DIR, PLANOGRAM_DIR, POS_DATA_DIR, DB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ─── Database ─────────────────────────────────────────────────
DATABASE_PATH = DB_DIR / "retail_shelf.db"

# ─── Redis ────────────────────────────────────────────────────
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_AVAILABLE = False  # Will be set dynamically

# ─── Computer Vision ─────────────────────────────────────────
# Custom-trained YOLOv8 on SKU-110K retail dataset (mAP50: 85.4%, Precision: 88.4%)
_CUSTOM_WEIGHTS = BASE_DIR / "weights" / "shelfiq_best.pt"
YOLO_MODEL = os.getenv(
    "YOLO_MODEL",
    str(_CUSTOM_WEIGHTS) if _CUSTOM_WEIGHTS.exists() else "yolov8n.pt"
)
# Base COCO model for person/general object detection (80 classes including 'person')
YOLO_COCO_MODEL = os.getenv("YOLO_COCO_MODEL", "yolov8n.pt")
DETECTION_CONFIDENCE = 0.35
DETECTION_IOU_THRESHOLD = 0.45
IMAGE_SIZE = 640

# ─── Stock Level Thresholds ──────────────────────────────────
STOCK_FULL_THRESHOLD = 0.7   # >= 70% of expected facings
STOCK_LOW_THRESHOLD = 0.3    # >= 30% but < 70%
# Below 30% = EMPTY

# ─── Forecasting ─────────────────────────────────────────────
FORECAST_HORIZON_DAYS = 30
LEAD_TIME_DAYS = 3
SERVICE_LEVEL = 0.95          # z-score ≈ 1.645 for 95% service level
Z_SCORE_95 = 1.645
SEASONALITY_MODE = "multiplicative"

# ─── Alerts ───────────────────────────────────────────────────
ALERT_COOLDOWN_MINUTES = 30   # Suppress duplicate alerts within this window
ALERT_CHANNELS = ["dashboard", "email"]  # Enabled notification channels
STOCKOUT_SEVERITY = 5
LOW_STOCK_SEVERITY = 3
PLANOGRAM_VIOLATION_SEVERITY = 2
PRICE_MISMATCH_SEVERITY = 1

# ─── Email (for alert digests) ────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL_RECIPIENTS = os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",")

# ─── Store Layout ─────────────────────────────────────────────
STORE_CONFIG = {
    "STORE01": {
        "name": "Mumbai Flagship Store",
        "aisles": 6,
        "shelves_per_aisle": 4,
        "sections_per_shelf": 5,
    },
    "STORE02": {
        "name": "Ahmedabad CG Road Outlet",
        "aisles": 4,
        "shelves_per_aisle": 3,
        "sections_per_shelf": 4,
    },
    "STORE03": {
        "name": "Delhi Connaught Place Superstore",
        "aisles": 8,
        "shelves_per_aisle": 5,
        "sections_per_shelf": 6,
    },
}

# ─── Product Catalog ─────────────────────────────────────────
CATEGORIES = [
    "Beverages", "Snacks", "Dairy", "Bakery", "Canned Goods",
    "Frozen Foods", "Personal Care", "Household", "Condiments", "Cereals"
]

NUM_SKUS = 50
NUM_STORES = 3
POS_HISTORY_DAYS = 730  # 2 years

# ─── Dashboard ────────────────────────────────────────────────
DASHBOARD_REFRESH_INTERVAL = 30  # seconds
STREAMLIT_PAGE_TITLE = "ShelfIQ — Retail Shelf Intelligence"
STREAMLIT_PAGE_ICON = "🛒"
STREAMLIT_LAYOUT = "wide"

# ─── Shelf Optimizer ─────────────────────────────────────────
OPTIMIZER_OUTPUT_DIR = DATA_DIR / "optimized_planograms"
OPTIMIZER_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
EYE_LEVEL_SHELVES: list[int] = [2, 3]          # 1-indexed shelf numbers considered "eye level"
TOP_PERFORMER_PERCENTILE: float = 0.80          # top 20% = above 80th percentile
ENGAGEMENT_DATA_PATH = POS_DATA_DIR / "customer_engagement.csv"
# Composite score weights (must sum to 1.0)
SCORE_WEIGHT_VELOCITY: float = 0.40
SCORE_WEIGHT_PROFIT: float = 0.35
SCORE_WEIGHT_ENGAGEMENT: float = 0.25
# Visibility multipliers by shelf position (1-indexed)
SHELF_VISIBILITY_MULTIPLIER: dict[int, float] = {
    1: 0.7,   # bottom shelf — low visibility
    2: 1.3,   # eye level — high visibility
    3: 1.5,   # prime eye level — highest visibility
    4: 1.0,   # upper shelf — moderate
    5: 0.8,   # top shelf — lower visibility
}
