"""
Database table definitions and schema management for the Retail Shelf Intelligence system.
Uses SQLite with raw SQL for simplicity and zero dependencies.
"""
import sqlite3
from pathlib import Path

SCHEMA_SQL = """
-- Product catalog
CREATE TABLE IF NOT EXISTS products (
    sku_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit_price REAL NOT NULL,
    avg_daily_demand REAL DEFAULT 0,
    shelf_life_days INTEGER DEFAULT 365,
    reorder_point REAL DEFAULT 0,
    safety_stock REAL DEFAULT 0,
    max_stock INTEGER DEFAULT 100,
    current_stock INTEGER DEFAULT 50,
    image_ref TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Store definitions
CREATE TABLE IF NOT EXISTS stores (
    store_id TEXT PRIMARY KEY,
    store_name TEXT NOT NULL,
    num_aisles INTEGER NOT NULL,
    shelves_per_aisle INTEGER NOT NULL,
    sections_per_shelf INTEGER NOT NULL,
    address TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shelf sections (granular shelf locations)
CREATE TABLE IF NOT EXISTS shelves (
    shelf_id TEXT PRIMARY KEY,
    store_id TEXT NOT NULL,
    aisle_id TEXT NOT NULL,
    shelf_number INTEGER NOT NULL,
    section_number INTEGER NOT NULL,
    assigned_sku TEXT,
    expected_facings INTEGER DEFAULT 3,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (assigned_sku) REFERENCES products(sku_id)
);

-- Detection results from CV pipeline
CREATE TABLE IF NOT EXISTS detections (
    detection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id TEXT NOT NULL,
    aisle_id TEXT NOT NULL,
    shelf_id TEXT NOT NULL,
    sku_id TEXT,
    confidence REAL,
    bbox_x REAL,
    bbox_y REAL,
    bbox_w REAL,
    bbox_h REAL,
    stock_level TEXT CHECK(stock_level IN ('FULL', 'LOW', 'EMPTY')) DEFAULT 'FULL',
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_path TEXT DEFAULT '',
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Alerts
CREATE TABLE IF NOT EXISTS alerts (
    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL CHECK(alert_type IN ('STOCKOUT','LOW_STOCK','PLANOGRAM_VIOLATION','PRICE_MISMATCH')),
    severity INTEGER NOT NULL DEFAULT 1,
    store_id TEXT NOT NULL,
    aisle_id TEXT DEFAULT '',
    shelf_id TEXT DEFAULT '',
    sku_id TEXT DEFAULT '',
    message TEXT NOT NULL,
    revenue_impact REAL DEFAULT 0,
    suggested_action TEXT DEFAULT '',
    priority_score REAL DEFAULT 0,
    acknowledged INTEGER DEFAULT 0,
    acknowledged_by TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    acknowledged_at TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Demand forecasts
CREATE TABLE IF NOT EXISTS forecasts (
    forecast_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    forecast_date TEXT NOT NULL,
    yhat REAL NOT NULL,
    yhat_lower REAL,
    yhat_upper REAL,
    actual REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES products(sku_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Replenishment orders
CREATE TABLE IF NOT EXISTS replenishment_orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku_id TEXT NOT NULL,
    store_id TEXT NOT NULL,
    order_quantity INTEGER NOT NULL,
    current_stock INTEGER DEFAULT 0,
    reorder_point REAL DEFAULT 0,
    status TEXT CHECK(status IN ('PENDING','APPROVED','IN_TRANSIT','DELIVERED','CANCELLED')) DEFAULT 'PENDING',
    priority TEXT CHECK(priority IN ('LOW','MEDIUM','HIGH','CRITICAL')) DEFAULT 'MEDIUM',
    estimated_delivery TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sku_id) REFERENCES products(sku_id),
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Planogram compliance reports
CREATE TABLE IF NOT EXISTS compliance_reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id TEXT NOT NULL,
    aisle_id TEXT NOT NULL,
    shelf_id TEXT DEFAULT '',
    compliance_score REAL NOT NULL,
    total_sections INTEGER DEFAULT 0,
    correct_sections INTEGER DEFAULT 0,
    misplaced_products INTEGER DEFAULT 0,
    missing_facings INTEGER DEFAULT 0,
    unauthorized_products INTEGER DEFAULT 0,
    price_mismatches INTEGER DEFAULT 0,
    details_json TEXT DEFAULT '{}',
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- POS transactions (aggregated daily)
CREATE TABLE IF NOT EXISTS pos_transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    store_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    product_name TEXT,
    category TEXT,
    quantity_sold INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    revenue REAL NOT NULL,
    promotion_flag INTEGER DEFAULT 0,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (sku_id) REFERENCES products(sku_id)
);

-- Weather data (for forecast enrichment)
CREATE TABLE IF NOT EXISTS weather_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    store_id TEXT NOT NULL,
    temperature_c REAL,
    precipitation_mm REAL,
    humidity_pct REAL,
    weather_condition TEXT,
    is_holiday INTEGER DEFAULT 0,
    local_event TEXT DEFAULT '',
    FOREIGN KEY (store_id) REFERENCES stores(store_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_detections_store ON detections(store_id, detected_at);
CREATE INDEX IF NOT EXISTS idx_alerts_store ON alerts(store_id, created_at);
CREATE INDEX IF NOT EXISTS idx_forecasts_sku ON forecasts(sku_id, store_id, forecast_date);
CREATE INDEX IF NOT EXISTS idx_pos_date ON pos_transactions(date, store_id, sku_id);
CREATE INDEX IF NOT EXISTS idx_weather_date ON weather_data(date, store_id);
CREATE INDEX IF NOT EXISTS idx_compliance_store ON compliance_reports(store_id, checked_at);

-- Customer engagement (views vs picks for shelf optimization)
CREATE TABLE IF NOT EXISTS customer_engagement (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    store_id TEXT NOT NULL,
    sku_id TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    impression_count INTEGER NOT NULL,
    pick_count INTEGER NOT NULL,
    conversion_rate REAL NOT NULL,
    FOREIGN KEY (store_id) REFERENCES stores(store_id),
    FOREIGN KEY (sku_id) REFERENCES products(sku_id)
);
CREATE INDEX IF NOT EXISTS idx_engagement_store_sku ON customer_engagement(store_id, sku_id);
"""


def create_tables(db_path: Path) -> None:
    """Create all database tables."""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()


def get_table_names(db_path: Path) -> list:
    """Return list of table names in the database."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables
