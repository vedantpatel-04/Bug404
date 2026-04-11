"""
Reorder point and safety stock calculator.
Uses forecast data and demand variability to determine optimal reorder points.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from dataclasses import dataclass
from config.settings import LEAD_TIME_DAYS, Z_SCORE_95, SERVICE_LEVEL


@dataclass
class ReorderPointResult:
    """Reorder point calculation result for a SKU."""
    sku_id: str
    store_id: str
    avg_daily_demand: float
    std_daily_demand: float
    lead_time_days: int
    safety_stock: float
    reorder_point: float
    max_stock: int
    current_stock: int
    needs_reorder: bool
    days_until_stockout: float
    service_level: float


class ReorderCalculator:
    """
    Calculates reorder points and safety stock using demand forecasts.

    Formulas:
        Safety Stock = z_score × σ_demand × √(lead_time)
        Reorder Point = (avg_daily_demand × lead_time) + safety_stock
    """

    def __init__(
        self,
        lead_time: int = LEAD_TIME_DAYS,
        service_level: float = SERVICE_LEVEL,
        z_score: float = Z_SCORE_95,
    ):
        self.lead_time = lead_time
        self.service_level = service_level
        self.z_score = z_score

    def calculate(
        self,
        sku_id: str,
        store_id: str,
        daily_demand: list,
        current_stock: int = 50,
        max_stock: int = 100,
    ) -> ReorderPointResult:
        """
        Calculate reorder point for a specific SKU.

        Args:
            sku_id: SKU identifier.
            store_id: Store identifier.
            daily_demand: List of daily demand values (historical or forecast).
            current_stock: Current inventory level.
            max_stock: Maximum shelf/storage capacity.

        Returns:
            ReorderPointResult.
        """
        demand = np.array(daily_demand, dtype=float)

        if len(demand) == 0:
            return ReorderPointResult(
                sku_id=sku_id, store_id=store_id,
                avg_daily_demand=0, std_daily_demand=0,
                lead_time_days=self.lead_time, safety_stock=0,
                reorder_point=0, max_stock=max_stock,
                current_stock=current_stock, needs_reorder=False,
                days_until_stockout=999, service_level=self.service_level,
            )

        avg_demand = np.mean(demand)
        std_demand = np.std(demand)

        # Safety stock calculation
        safety_stock = self.z_score * std_demand * np.sqrt(self.lead_time)

        # Reorder point
        rop = (avg_demand * self.lead_time) + safety_stock

        # Days until stockout
        if avg_demand > 0:
            days_until_stockout = current_stock / avg_demand
        else:
            days_until_stockout = 999

        needs_reorder = current_stock <= rop

        return ReorderPointResult(
            sku_id=sku_id,
            store_id=store_id,
            avg_daily_demand=round(avg_demand, 2),
            std_daily_demand=round(std_demand, 2),
            lead_time_days=self.lead_time,
            safety_stock=round(safety_stock, 2),
            reorder_point=round(rop, 2),
            max_stock=max_stock,
            current_stock=current_stock,
            needs_reorder=needs_reorder,
            days_until_stockout=round(days_until_stockout, 1),
            service_level=self.service_level,
        )

    def batch_calculate(self, sku_demand_data: list) -> list:
        """
        Calculate reorder points for multiple SKUs.

        Args:
            sku_demand_data: List of dicts with keys:
                sku_id, store_id, daily_demand, current_stock, max_stock

        Returns:
            List of ReorderPointResult.
        """
        results = []
        for item in sku_demand_data:
            result = self.calculate(
                sku_id=item["sku_id"],
                store_id=item["store_id"],
                daily_demand=item["daily_demand"],
                current_stock=item.get("current_stock", 50),
                max_stock=item.get("max_stock", 100),
            )
            results.append(result)
        return results

    def simulate_reorder_data(self, num_skus: int = 20) -> list:
        """Generate simulated reorder data for demo."""
        np.random.seed(42)
        results = []
        for i in range(num_skus):
            sku_id = f"SKU{i + 1:03d}"
            avg = np.random.uniform(5, 35)
            std = avg * np.random.uniform(0.1, 0.4)
            demand = np.random.normal(avg, std, 30).clip(0).tolist()
            current_stock = int(np.random.uniform(5, 100))
            max_stock = int(np.random.uniform(80, 200))

            result = self.calculate(
                sku_id=sku_id,
                store_id="STORE01",
                daily_demand=demand,
                current_stock=current_stock,
                max_stock=max_stock,
            )
            results.append(result)
        return results
