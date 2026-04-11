"""
SQLite database manager — connection handling, CRUD helpers, and query utilities.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

import sys, os
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import DATABASE_PATH
from database.models import create_tables


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = str(db_path or DATABASE_PATH)
        self._ensure_tables()

    def _ensure_tables(self):
        create_tables(Path(self.db_path))

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def execute(self, query: str, params: tuple = ()) -> list:
        conn = self._connect()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def execute_many(self, query: str, params_list: list) -> None:
        conn = self._connect()
        try:
            conn.executemany(query, params_list)
            conn.commit()
        finally:
            conn.close()

    def insert(self, table: str, data: dict) -> int:
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        conn = self._connect()
        try:
            cursor = conn.execute(query, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def insert_many(self, table: str, data_list: list[dict]) -> None:
        if not data_list:
            return
        columns = ", ".join(data_list[0].keys())
        placeholders = ", ".join(["?"] * len(data_list[0]))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        params = [tuple(d.values()) for d in data_list]
        self.execute_many(query, params)

    def fetch_all(self, table: str, where: str = "", params: tuple = (), order_by: str = "", limit: int = 0) -> list:
        query = f"SELECT * FROM {table}"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit > 0:
            query += f" LIMIT {limit}"
        return self.execute(query, params)

    def fetch_one(self, table: str, where: str, params: tuple = ()) -> Optional[dict]:
        results = self.fetch_all(table, where, params, limit=1)
        return results[0] if results else None

    def update(self, table: str, data: dict, where: str, params: tuple = ()) -> None:
        set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        all_params = tuple(data.values()) + params
        self.execute(query, all_params)

    def count(self, table: str, where: str = "", params: tuple = ()) -> int:
        query = f"SELECT COUNT(*) as cnt FROM {table}"
        if where:
            query += f" WHERE {where}"
        result = self.execute(query, params)
        return result[0]["cnt"] if result else 0

    def get_products(self) -> list:
        return self.fetch_all("products", order_by="category, product_name")

    def get_stores(self) -> list:
        return self.fetch_all("stores")

    def get_active_alerts(self, store_id: str = "") -> list:
        where = "acknowledged = 0"
        params = ()
        if store_id:
            where += " AND store_id = ?"
            params = (store_id,)
        return self.fetch_all("alerts", where, params, order_by="priority_score DESC, created_at DESC")

    def get_recent_detections(self, store_id: str, limit: int = 100) -> list:
        return self.fetch_all(
            "detections",
            where="store_id = ?",
            params=(store_id,),
            order_by="detected_at DESC",
            limit=limit,
        )

    def get_pos_data(self, store_id: str = "", sku_id: str = "") -> list:
        where_parts = []
        params = []
        if store_id:
            where_parts.append("store_id = ?")
            params.append(store_id)
        if sku_id:
            where_parts.append("sku_id = ?")
            params.append(sku_id)
        where = " AND ".join(where_parts) if where_parts else ""
        return self.fetch_all("pos_transactions", where, tuple(params), order_by="date ASC")

    def get_forecasts(self, sku_id: str, store_id: str) -> list:
        return self.fetch_all(
            "forecasts",
            where="sku_id = ? AND store_id = ?",
            params=(sku_id, store_id),
            order_by="forecast_date ASC",
        )

    def get_compliance_reports(self, store_id: str = "") -> list:
        where = "store_id = ?" if store_id else ""
        params = (store_id,) if store_id else ()
        return self.fetch_all("compliance_reports", where, params, order_by="checked_at DESC")

    def get_replenishment_orders(self, status: str = "") -> list:
        where = "status = ?" if status else ""
        params = (status,) if status else ()
        return self.fetch_all("replenishment_orders", where, params, order_by="created_at DESC")

    def acknowledge_alert(self, alert_id: int, user: str = "system") -> None:
        self.update(
            "alerts",
            {"acknowledged": 1, "acknowledged_by": user, "acknowledged_at": datetime.now().isoformat()},
            "alert_id = ?",
            (alert_id,),
        )


# Singleton instance
db = DatabaseManager()
