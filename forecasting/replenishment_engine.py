"""
Replenishment engine — generates automated replenishment orders
based on reorder points and demand forecasts.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional

from forecasting.reorder_calculator import ReorderCalculator, ReorderPointResult


@dataclass
class ReplenishmentOrder:
    """A generated replenishment order."""
    sku_id: str
    store_id: str
    product_name: str
    order_quantity: int
    current_stock: int
    reorder_point: float
    safety_stock: float
    priority: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    estimated_delivery: str
    reason: str
    revenue_at_risk: float


class ReplenishmentEngine:
    """
    Generates automated replenishment orders when stock falls below reorder points.
    Prioritizes orders by urgency and revenue impact.
    """

    def __init__(self, lead_time_days: int = 3):
        self.calculator = ReorderCalculator(lead_time=lead_time_days)
        self.lead_time = lead_time_days

    def generate_orders(self, reorder_results: list, product_info: Optional[dict] = None) -> list:
        """
        Generate replenishment orders from reorder point results.

        Args:
            reorder_results: List of ReorderPointResult.
            product_info: Optional dict mapping sku_id to product details.

        Returns:
            List of ReplenishmentOrder, sorted by priority.
        """
        orders = []
        for result in reorder_results:
            if not result.needs_reorder:
                continue

            # Calculate order quantity
            order_qty = max(
                int(result.max_stock - result.current_stock),
                int(result.safety_stock * 2),
            )
            order_qty = max(order_qty, 1)

            # Determine priority
            if result.days_until_stockout <= 1:
                priority = "CRITICAL"
            elif result.days_until_stockout <= self.lead_time:
                priority = "HIGH"
            elif result.current_stock <= result.safety_stock:
                priority = "HIGH"
            elif result.current_stock <= result.reorder_point:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            # Estimated delivery
            delivery_date = datetime.now() + timedelta(days=self.lead_time)
            if priority == "CRITICAL":
                delivery_date = datetime.now() + timedelta(days=1)
            elif priority == "HIGH":
                delivery_date = datetime.now() + timedelta(days=2)

            # Revenue at risk
            revenue_at_risk = round(result.avg_daily_demand * result.days_until_stockout * 3.5, 2)
            if result.days_until_stockout <= 1:
                revenue_at_risk *= 3  # Higher for imminent stockouts

            # Product name
            name = f"Product {result.sku_id}"
            if product_info and result.sku_id in product_info:
                name = product_info[result.sku_id].get("product_name", name)

            reason = self._get_reason(result)

            orders.append(ReplenishmentOrder(
                sku_id=result.sku_id,
                store_id=result.store_id,
                product_name=name,
                order_quantity=order_qty,
                current_stock=result.current_stock,
                reorder_point=result.reorder_point,
                safety_stock=result.safety_stock,
                priority=priority,
                estimated_delivery=delivery_date.strftime("%Y-%m-%d"),
                reason=reason,
                revenue_at_risk=revenue_at_risk,
            ))

        # Sort by priority (CRITICAL > HIGH > MEDIUM > LOW)
        priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        orders.sort(key=lambda o: (priority_order.get(o.priority, 99), -o.revenue_at_risk))

        return orders

    def _get_reason(self, result: ReorderPointResult) -> str:
        """Generate human-readable reason for the order."""
        if result.days_until_stockout <= 0:
            return f"STOCKOUT IMMINENT — current stock ({result.current_stock}) depleted"
        elif result.days_until_stockout <= 1:
            return f"Critical: only {result.days_until_stockout:.1f} days of stock remaining"
        elif result.current_stock <= result.safety_stock:
            return f"Below safety stock ({result.current_stock} < {result.safety_stock:.0f})"
        else:
            return f"Below reorder point ({result.current_stock} < ROP {result.reorder_point:.0f})"

    def get_replenishment_summary(self, orders: list) -> dict:
        """Get summary statistics for generated orders."""
        if not orders:
            return {
                "total_orders": 0, "total_units": 0, "critical": 0,
                "high": 0, "medium": 0, "low": 0, "total_revenue_at_risk": 0,
            }

        return {
            "total_orders": len(orders),
            "total_units": sum(o.order_quantity for o in orders),
            "critical": sum(1 for o in orders if o.priority == "CRITICAL"),
            "high": sum(1 for o in orders if o.priority == "HIGH"),
            "medium": sum(1 for o in orders if o.priority == "MEDIUM"),
            "low": sum(1 for o in orders if o.priority == "LOW"),
            "total_revenue_at_risk": round(sum(o.revenue_at_risk for o in orders), 2),
            "avg_order_qty": round(np.mean([o.order_quantity for o in orders]), 1),
        }

    def simulate_orders(self, num_orders: int = 15) -> list:
        """Generate simulated replenishment orders for demo."""
        reorder_results = self.calculator.simulate_reorder_data(num_skus=num_orders * 2)
        # Product name lookup
        from data.generators.generate_pos_data import PRODUCT_NAMES
        product_info = {
            f"SKU{i + 1:03d}": {"product_name": name}
            for i, name in enumerate(PRODUCT_NAMES)
        }
        orders = self.generate_orders(reorder_results, product_info)
        return orders[:num_orders]
