"""Tests for demand forecasting module."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from forecasting.demand_forecaster import DemandForecaster
from forecasting.reorder_calculator import ReorderCalculator, ReorderPointResult
from forecasting.replenishment_engine import ReplenishmentEngine


class TestDemandForecaster(unittest.TestCase):
    """Tests for the DemandForecaster class."""

    def setUp(self):
        self.forecaster = DemandForecaster()

    def test_empty_forecast(self):
        """Empty input should return empty forecast."""
        result = self.forecaster.forecast(pd.DataFrame(), "SKU001", "STORE01")
        self.assertIsInstance(result, pd.DataFrame)
        self.assertIn("yhat", result.columns)

    def test_fallback_forecast(self):
        """Test fallback forecasting with synthetic data."""
        dates = pd.date_range(end=datetime.now(), periods=90, freq="D")
        data = pd.DataFrame({
            "ds": dates,
            "y": np.random.poisson(20, 90).astype(float),
        })
        result = self.forecaster.forecast(data, "SKU001", "STORE01", horizon_days=14)
        self.assertGreater(len(result), 0)
        self.assertIn("yhat", result.columns)
        self.assertIn("yhat_lower", result.columns)
        self.assertIn("yhat_upper", result.columns)

    def test_accuracy_metrics(self):
        """Test forecast accuracy calculation."""
        actual = pd.Series([10, 20, 15, 25, 30])
        predicted = pd.Series([12, 18, 14, 22, 28])
        metrics = self.forecaster.calculate_accuracy(actual, predicted)
        self.assertIn("mae", metrics)
        self.assertIn("rmse", metrics)
        self.assertIn("wmape", metrics)
        self.assertGreater(metrics["mae"], 0)

    def test_accuracy_with_zeros(self):
        """Accuracy should handle zero actuals."""
        actual = pd.Series([0, 0, 0])
        predicted = pd.Series([1, 2, 3])
        metrics = self.forecaster.calculate_accuracy(actual, predicted)
        self.assertEqual(metrics["mae"], 0)  # All masked out

    def test_simulate_results(self):
        """Test simulation mode."""
        result = self.forecaster.simulate_forecast_results("SKU001", "STORE01", days=60)
        self.assertEqual(len(result), 60)
        self.assertIn("actual", result.columns)
        self.assertIn("yhat", result.columns)


class TestReorderCalculator(unittest.TestCase):
    """Tests for the ReorderCalculator class."""

    def setUp(self):
        self.calculator = ReorderCalculator()

    def test_basic_calculation(self):
        """Test basic reorder point calculation."""
        result = self.calculator.calculate(
            sku_id="SKU001",
            store_id="STORE01",
            daily_demand=[10, 12, 8, 15, 11, 9, 13],
            current_stock=20,
            max_stock=100,
        )
        self.assertIsInstance(result, ReorderPointResult)
        self.assertGreater(result.reorder_point, 0)
        self.assertGreater(result.safety_stock, 0)

    def test_needs_reorder(self):
        """Test reorder flag when stock is low."""
        result = self.calculator.calculate(
            sku_id="SKU001",
            store_id="STORE01",
            daily_demand=[20, 25, 22, 18, 23],
            current_stock=5,  # Very low
            max_stock=100,
        )
        self.assertTrue(result.needs_reorder)

    def test_no_reorder_needed(self):
        """Test that high stock doesn't trigger reorder."""
        result = self.calculator.calculate(
            sku_id="SKU001",
            store_id="STORE01",
            daily_demand=[5, 4, 6, 3, 5],
            current_stock=90,  # Plenty of stock
            max_stock=100,
        )
        self.assertFalse(result.needs_reorder)

    def test_empty_demand(self):
        """Test with empty demand data."""
        result = self.calculator.calculate("SKU001", "STORE01", [], current_stock=50)
        self.assertEqual(result.reorder_point, 0)
        self.assertFalse(result.needs_reorder)

    def test_batch_calculate(self):
        """Test batch calculation."""
        items = [
            {"sku_id": "SKU001", "store_id": "STORE01", "daily_demand": [10, 12, 8], "current_stock": 5},
            {"sku_id": "SKU002", "store_id": "STORE01", "daily_demand": [20, 22, 18], "current_stock": 80},
        ]
        results = self.calculator.batch_calculate(items)
        self.assertEqual(len(results), 2)


class TestReplenishmentEngine(unittest.TestCase):
    """Tests for the ReplenishmentEngine."""

    def setUp(self):
        self.engine = ReplenishmentEngine()

    def test_generate_orders(self):
        """Test order generation."""
        results = self.engine.calculator.simulate_reorder_data(20)
        orders = self.engine.generate_orders(results)
        # Should generate some orders (not all SKUs need reorder)
        self.assertIsInstance(orders, list)

    def test_order_priority(self):
        """Test that orders are sorted by priority."""
        orders = self.engine.simulate_orders(10)
        if len(orders) >= 2:
            priority_map = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            for i in range(len(orders) - 1):
                p1 = priority_map.get(orders[i].priority, 99)
                p2 = priority_map.get(orders[i + 1].priority, 99)
                self.assertLessEqual(p1, p2)

    def test_summary(self):
        """Test order summary generation."""
        orders = self.engine.simulate_orders(10)
        summary = self.engine.get_replenishment_summary(orders)
        self.assertIn("total_orders", summary)
        self.assertIn("total_units", summary)
        self.assertIn("critical", summary)


if __name__ == "__main__":
    unittest.main()
