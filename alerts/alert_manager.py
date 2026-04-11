"""
Alert manager — creates, prioritizes, deduplicates, and manages alerts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from datetime import datetime, timedelta
from typing import Optional

from alerts.alert_models import Alert, SUGGESTED_ACTIONS, generate_corrective_action
from config.settings import (
    ALERT_COOLDOWN_MINUTES, STOCKOUT_SEVERITY,
    LOW_STOCK_SEVERITY, PLANOGRAM_VIOLATION_SEVERITY, PRICE_MISMATCH_SEVERITY,
)


class AlertManager:
    """
    Creates, prioritizes, and manages alerts.
    Handles deduplication and cooldown periods.
    """

    def __init__(self):
        self.recent_alerts = {}  # key -> timestamp (for dedup)
        self.cooldown = timedelta(minutes=ALERT_COOLDOWN_MINUTES)

    def create_alert(
        self,
        alert_type: str,
        store_id: str,
        message: str,
        aisle_id: str = "",
        shelf_id: str = "",
        sku_id: str = "",
        revenue_impact: float = 0.0,
    ) -> Optional[Alert]:
        """
        Create a new alert if not a duplicate within cooldown period.

        Returns:
            Alert object, or None if suppressed as duplicate.
        """
        # Dedup key
        dedup_key = f"{alert_type}:{store_id}:{aisle_id}:{shelf_id}:{sku_id}"
        now = datetime.now()

        # Check cooldown
        if dedup_key in self.recent_alerts:
            last_time = self.recent_alerts[dedup_key]
            if now - last_time < self.cooldown:
                return None  # Suppress duplicate

        # Get severity
        severity_map = {
            "STOCKOUT": STOCKOUT_SEVERITY,
            "LOW_STOCK": LOW_STOCK_SEVERITY,
            "PLANOGRAM_VIOLATION": PLANOGRAM_VIOLATION_SEVERITY,
            "PRICE_MISMATCH": PRICE_MISMATCH_SEVERITY,
        }
        severity = severity_map.get(alert_type, 2)

        # Calculate priority score
        recency_factor = 1.0
        priority_score = severity * max(revenue_impact, 1) * recency_factor

        # Get suggested action
        actions = SUGGESTED_ACTIONS.get(alert_type, ["Investigate and resolve"])
        suggested = actions[0] if actions else "Investigate and resolve"

        # Generate context-aware corrective action (CHANGE 5)
        corrective = generate_corrective_action(
            alert_type=alert_type,
            sku_id=sku_id,
            aisle_id=aisle_id,
            shelf_id=shelf_id,
        )

        alert = Alert(
            alert_type=alert_type,
            severity=severity,
            store_id=store_id,
            aisle_id=aisle_id,
            shelf_id=shelf_id,
            sku_id=sku_id,
            message=message,
            revenue_impact=round(revenue_impact, 2),
            suggested_action=suggested,
            corrective_action=corrective,
            priority_score=round(priority_score, 2),
            created_at=now.isoformat(),
        )

        self.recent_alerts[dedup_key] = now
        return alert

    def prioritize_alerts(self, alerts: list) -> list:
        """Sort alerts by priority score (highest first)."""
        return sorted(alerts, key=lambda a: a.priority_score if isinstance(a, Alert) else a.get("priority_score", 0), reverse=True)

    def save_alert(self, alert: Alert) -> int:
        """Save alert to database."""
        try:
            from database.db_manager import db
            alert_id = db.insert("alerts", {
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "store_id": alert.store_id,
                "aisle_id": alert.aisle_id,
                "shelf_id": alert.shelf_id,
                "sku_id": alert.sku_id,
                "message": alert.message,
                "revenue_impact": alert.revenue_impact,
                "suggested_action": alert.suggested_action,
                "priority_score": alert.priority_score,
            })
            return alert_id
        except Exception as e:
            print(f"  ⚠ Could not save alert: {e}")
            return 0

    def get_active_alerts(self, store_id: str = "") -> list:
        """Get all unacknowledged alerts."""
        try:
            from database.db_manager import db
            rows = db.get_active_alerts(store_id)
            return [Alert.from_dict(r) for r in rows]
        except Exception:
            return []

    def acknowledge_alert(self, alert_id: int, user: str = "system"):
        """Mark an alert as acknowledged."""
        try:
            from database.db_manager import db
            db.acknowledge_alert(alert_id, user)
        except Exception as e:
            print(f"  ⚠ Could not acknowledge alert: {e}")

    def generate_sample_alerts(self, store_id: str = "STORE01", count: int = 10) -> list:
        """Generate sample alerts for demo purposes."""
        np.random.seed(hash(store_id) % 2**31)
        alerts = []
        alert_templates = [
            ("STOCKOUT", "Coca-Cola 500ml out of stock", "SKU001", 5, 150),
            ("LOW_STOCK", "Lay's Classic Chips running low (2 units)", "SKU006", 3, 45),
            ("STOCKOUT", "Whole Milk 1L depleted", "SKU011", 5, 200),
            ("PLANOGRAM_VIOLATION", "Doritos placed in Beverages section", "SKU007", 2, 20),
            ("PRICE_MISMATCH", "Greek Yogurt price tag shows $3.99, should be $4.99", "SKU012", 1, 15),
            ("STOCKOUT", "White Bread Loaf empty shelf", "SKU016", 5, 180),
            ("LOW_STOCK", "Ketchup 500ml below threshold", "SKU041", 3, 35),
            ("PLANOGRAM_VIOLATION", "Unauthorized product found in Aisle 3", "", 4, 30),
            ("STOCKOUT", "Frozen Pizza Margherita out of stock", "SKU026", 5, 250),
            ("LOW_STOCK", "Shampoo 400ml at minimum level", "SKU031", 3, 55),
        ]

        for i in range(min(count, len(alert_templates))):
            atype, msg, sku, sev, impact = alert_templates[i]
            aid = f"A{np.random.randint(1, 7):02d}"
            sid = f"S{np.random.randint(1, 5):02d}"

            # Generate corrective action (CHANGE 5)
            corrective = generate_corrective_action(
                alert_type=atype,
                sku_id=sku,
                aisle_id=aid,
                shelf_id=sid,
            )

            alert = Alert(
                alert_id=i + 1,
                alert_type=atype,
                severity=sev,
                store_id=store_id,
                aisle_id=aid,
                shelf_id=sid,
                sku_id=sku,
                message=msg,
                revenue_impact=impact + np.random.uniform(-20, 50),
                suggested_action=SUGGESTED_ACTIONS.get(atype, ["Investigate"])[0],
                corrective_action=corrective,
                priority_score=sev * impact * np.random.uniform(0.8, 1.2),
                created_at=(datetime.now() - timedelta(minutes=np.random.randint(1, 120))).isoformat(),
            )
            alerts.append(alert)

        return self.prioritize_alerts(alerts)
