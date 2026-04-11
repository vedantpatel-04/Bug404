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
    corrective_action: str = ""    # Detailed corrective action (CHANGE 5)
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
            "corrective_action": self.corrective_action,
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
            corrective_action=data.get("corrective_action", ""),
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


def generate_corrective_action(
    alert_type: str,
    sku_id: str = "",
    sku_name: str = "",
    aisle_id: str = "",
    shelf_id: str = "",
    detected_price: float = 0.0,
    expected_price: float = 0.0,
    current_position: str = "",
    correct_position: str = "",
    reorder_qty: int = 0,
    hours_to_stockout: int = 0,
) -> str:
    """
    Generate a detailed, actionable corrective action string based on alert type.
    (CHANGE 5) — Provides specific instructions for store associates.
    """
    product = sku_name or sku_id or "Unknown product"
    location = f"Aisle {aisle_id}, Shelf {shelf_id}" if aisle_id else "unknown location"
    qty = reorder_qty if reorder_qty > 0 else 12  # sensible default

    if alert_type == "STOCKOUT":
        return (
            f"Restock {product} at {location}. "
            f"Suggested reorder qty: {qty} units. "
            f"Contact supplier: auto-replenishment triggered."
        )

    elif alert_type == "PLANOGRAM_VIOLATION":
        cur = current_position or location
        cor = correct_position or "correct position per planogram layout"
        return (
            f"Move {product} from {cur} to {cor} per planogram layout."
        )

    elif alert_type == "LOW_STOCK":
        hrs = hours_to_stockout if hours_to_stockout > 0 else 4
        return (
            f"Schedule replenishment for {product} within {hrs} hours to avoid stockout. "
            f"Current location: {location}."
        )

    elif alert_type == "PRICE_MISMATCH":
        det = f"${detected_price:.2f}" if detected_price > 0 else "detected price"
        exp = f"${expected_price:.2f}" if expected_price > 0 else "planogram price"
        return (
            f"Update price tag at {location} from {det} to {exp}."
        )

    return f"Investigate alert for {product} at {location} and resolve."
