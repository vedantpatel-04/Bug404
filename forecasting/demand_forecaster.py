"""
Prophet-based demand forecaster.
Predicts product-level demand at each store location with seasonality,
holidays, and external regressors.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional

from config.settings import FORECAST_HORIZON_DAYS, SEASONALITY_MODE


class DemandForecaster:
    """
    Prophet-based demand forecasting with support for external regressors.
    Falls back to simple exponential smoothing if Prophet is not available.
    """

    def __init__(self):
        self.models = {}  # (sku_id, store_id) -> fitted model
        self.prophet_available = False
        try:
            from prophet import Prophet
            self.prophet_available = True
        except ImportError:
            print("  ⚠ Prophet not available. Using fallback forecaster.")

    def forecast(
        self,
        data: pd.DataFrame,
        sku_id: str,
        store_id: str,
        horizon_days: int = FORECAST_HORIZON_DAYS,
    ) -> pd.DataFrame:
        """
        Forecast demand for a specific SKU at a store.

        Args:
            data: DataFrame with columns ['ds', 'y'] and optional regressors.
            sku_id: SKU identifier.
            store_id: Store identifier.
            horizon_days: Number of days to forecast ahead.

        Returns:
            DataFrame with columns ['ds', 'yhat', 'yhat_lower', 'yhat_upper'].
        """
        if data.empty or len(data) < 14:
            return self._empty_forecast(horizon_days)

        if self.prophet_available:
            return self._prophet_forecast(data, sku_id, store_id, horizon_days)
        else:
            return self._fallback_forecast(data, horizon_days)

    def _prophet_forecast(self, data: pd.DataFrame, sku_id: str, store_id: str, horizon_days: int) -> pd.DataFrame:
        """Run Prophet forecast."""
        from prophet import Prophet

        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            seasonality_mode=SEASONALITY_MODE,
            changepoint_prior_scale=0.05,
            interval_width=0.9,
        )

        # Add regressors if available (CHANGE 7: added event regressors)
        regressors = []
        for col in ["promotion", "temperature", "holiday_flag", "is_local_event", "event_magnitude"]:
            if col in data.columns:
                model.add_regressor(col)
                regressors.append(col)

        # Fit model
        train_data = data[["ds", "y"] + regressors].copy()
        train_data["ds"] = pd.to_datetime(train_data["ds"])
        model.fit(train_data)

        # Generate future dataframe
        future = model.make_future_dataframe(periods=horizon_days, freq="D")

        # Fill regressor values for future dates
        for reg in regressors:
            if reg in data.columns:
                last_val = data[reg].iloc[-1] if len(data) > 0 else 0
                future[reg] = future["ds"].map(
                    dict(zip(data["ds"], data[reg]))
                ).fillna(last_val)

        # Predict
        forecast = model.predict(future)
        self.models[(sku_id, store_id)] = model

        result = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        result["yhat"] = result["yhat"].clip(lower=0)
        result["yhat_lower"] = result["yhat_lower"].clip(lower=0)
        result["yhat_upper"] = result["yhat_upper"].clip(lower=0)

        return result

    def _fallback_forecast(self, data: pd.DataFrame, horizon_days: int) -> pd.DataFrame:
        """Simple exponential smoothing fallback when Prophet is unavailable."""
        y = data["y"].values.astype(float)
        alpha = 0.3

        # Simple exponential smoothing
        smoothed = [y[0]]
        for i in range(1, len(y)):
            smoothed.append(alpha * y[i] + (1 - alpha) * smoothed[-1])

        last_value = smoothed[-1]
        std = np.std(y[-30:]) if len(y) >= 30 else np.std(y)

        # Calculate weekly pattern
        weekly = np.zeros(7)
        counts = np.zeros(7)
        dates = pd.to_datetime(data["ds"])
        for i, date in enumerate(dates):
            dow = date.dayofweek
            weekly[dow] += y[i]
            counts[dow] += 1
        weekly_avg = weekly / np.maximum(counts, 1)
        weekly_factor = weekly_avg / max(np.mean(weekly_avg), 0.01)

        # Generate forecast
        last_date = pd.to_datetime(data["ds"].iloc[-1])
        forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=horizon_days, freq="D")

        # Historical + forecast
        all_dates = list(pd.to_datetime(data["ds"])) + list(forecast_dates)
        all_yhat = list(y)
        all_lower = list(y - std)
        all_upper = list(y + std)

        for i, date in enumerate(forecast_dates):
            dow = date.dayofweek
            pred = last_value * weekly_factor[dow]
            noise = np.random.normal(0, std * 0.1)
            pred = max(0, pred + noise)
            all_yhat.append(round(pred, 2))
            all_lower.append(round(max(0, pred - 1.5 * std), 2))
            all_upper.append(round(pred + 1.5 * std, 2))

        return pd.DataFrame({
            "ds": all_dates,
            "yhat": all_yhat,
            "yhat_lower": all_lower,
            "yhat_upper": all_upper,
        })

    def _empty_forecast(self, horizon_days: int) -> pd.DataFrame:
        """Return empty forecast DataFrame."""
        dates = pd.date_range(start=datetime.now(), periods=horizon_days, freq="D")
        return pd.DataFrame({
            "ds": dates,
            "yhat": [0] * horizon_days,
            "yhat_lower": [0] * horizon_days,
            "yhat_upper": [0] * horizon_days,
        })

    def calculate_accuracy(self, actual: pd.Series, predicted: pd.Series) -> dict:
        """
        Calculate forecast accuracy metrics.

        Returns:
            Dict with MAE, RMSE, WMAPE, and MAPE.
        """
        actual = np.array(actual, dtype=float)
        predicted = np.array(predicted, dtype=float)
        mask = actual > 0

        if mask.sum() == 0:
            return {"mae": 0, "rmse": 0, "wmape": 0, "mape": 0}

        errors = actual[mask] - predicted[mask]
        abs_errors = np.abs(errors)

        mae = np.mean(abs_errors)
        rmse = np.sqrt(np.mean(errors ** 2))
        wmape = np.sum(abs_errors) / np.sum(actual[mask]) * 100
        mape = np.mean(abs_errors / actual[mask]) * 100

        return {
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "wmape": round(wmape, 2),
            "mape": round(min(mape, 999), 2),
        }

    def simulate_forecast_results(self, sku_id: str, store_id: str, days: int = 90) -> pd.DataFrame:
        """Generate simulated forecast data for dashboard demo."""
        np.random.seed(hash(f"{sku_id}{store_id}") % 2**31)

        dates = pd.date_range(end=datetime.now() + timedelta(days=30), periods=days, freq="D")
        base = np.random.uniform(10, 40)

        # Actual values (historical portion)
        actuals = []
        forecasts = []
        for i, date in enumerate(dates):
            dow_factor = 1.3 if date.dayofweek >= 5 else 1.0
            seasonal = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)
            noise = np.random.normal(0, base * 0.15)
            actual = max(0, base * dow_factor * seasonal + noise)
            actuals.append(round(actual, 1))

            # Forecast with slight error
            forecast_noise = np.random.normal(0, base * 0.1)
            pred = max(0, actual + forecast_noise)
            forecasts.append(round(pred, 1))

        std = np.std(actuals) * 0.8

        return pd.DataFrame({
            "ds": dates,
            "actual": actuals,
            "yhat": forecasts,
            "yhat_lower": [max(0, f - std) for f in forecasts],
            "yhat_upper": [f + std for f in forecasts],
            "is_forecast": [1 if d > pd.Timestamp.now() else 0 for d in dates],
        })
