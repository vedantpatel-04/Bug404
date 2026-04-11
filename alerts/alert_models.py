"""
Alert data models and types.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AlertType(str, Enum):
    STOCKOUT = "STOCKOUT"
    LOW_STOCK = "LOW_STOCK"
    PLANOGRAM_VIOLATION = "PLANOGRAM_VIOLATION"
    PRICE_MISMATCH = "PRICE_MISMATCH"


class AlertSeverity(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


@dataclass
class Alert:
    """A retail shelf alert."""
    alert_id: int = 0
    alert_type: str = ""
    severity: int = 1
    store_id: str = ""
    aisle_id: str = ""
    shelf_id: str = ""
    sku_id: str = ""
    message: str = ""
    revenue_impact: float = 0.0
    suggested_action: str = ""
    priority_score: float = 0.0
    acknowledged: bool = False
    acknowledged_by: str = ""
    created_at: str = ""
    acknowledged_at: str = ""

    def to_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "store_id": self.store_id,
            "aisle_id": self.aisle_id,
            "shelf_id": self.shelf_id,
            "sku_id": self.sku_id,
            "message": self.message,
            "revenue_impact": self.revenue_impact,
            "suggested_action": self.suggested_action,
            "priority_score": self.priority_score,
            "acknowledged": self.acknowledged,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "Alert":
        return Alert(
            alert_id=data.get("alert_id", 0),
            alert_type=data.get("alert_type", ""),
            severity=data.get("severity", 1),
            store_id=data.get("store_id", ""),
            aisle_id=data.get("aisle_id", ""),
            shelf_id=data.get("shelf_id", ""),
            sku_id=data.get("sku_id", ""),
            message=data.get("message", ""),
            revenue_impact=data.get("revenue_impact", 0),
            suggested_action=data.get("suggested_action", ""),
            priority_score=data.get("priority_score", 0),
            acknowledged=bool(data.get("acknowledged", 0)),
            acknowledged_by=data.get("acknowledged_by", ""),
            created_at=data.get("created_at", ""),
            acknowledged_at=data.get("acknowledged_at", ""),
        )


SUGGESTED_ACTIONS = {
    "STOCKOUT": [
        "Check backroom inventory and restock immediately",
        "Verify if product is on incoming delivery schedule",
        "Consider substitute product placement",
        "Notify warehouse for emergency replenishment",
    ],
    "LOW_STOCK": [
        "Schedule restocking during next associate pass",
        "Check backroom for available cases",
        "Monitor during peak hours",
    ],
    "PLANOGRAM_VIOLATION": [
        "Return misplaced product to correct location",
        "Verify product label and shelf tag match",
        "Report to category manager if recurring",
    ],
    "PRICE_MISMATCH": [
        "Update shelf tag to match POS system price",
        "Verify promotional pricing schedule",
        "Check for expired promotion tags",
    ],
}
