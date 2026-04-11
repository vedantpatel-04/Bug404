"""
Feature engineering for demand forecasting.
Merges POS data with weather, promotions, events, and calendar features.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from config.settings import POS_DATA_DIR


def load_pos_data() -> pd.DataFrame:
    """Load POS transaction data."""
    path = POS_DATA_DIR / "pos_transactions.csv"
    if path.exists():
        df = pd.read_csv(path, parse_dates=["date"])
        return df
    return pd.DataFrame()


def load_weather_data() -> pd.DataFrame:
    """Load weather and event data."""
    path = POS_DATA_DIR / "weather_data.csv"
    if path.exists():
        df = pd.read_csv(path, parse_dates=["date"])
        return df
    return pd.DataFrame()


def engineer_features(pos_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create features for demand forecasting.

    Adds calendar features, lag features, rolling stats, and weather data.
    """
    if pos_df.empty:
        return pos_df

    df = pos_df.copy()
    df["date"] = pd.to_datetime(df["date"])

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek
    df["day_of_month"] = df["date"].dt.day
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_month_start"] = df["date"].dt.is_month_start.astype(int)
    df["is_month_end"] = df["date"].dt.is_month_end.astype(int)
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)

    # Sort by sku and date for lag calculation
    df = df.sort_values(["store_id", "sku_id", "date"])

    # Lag features (per SKU per store)
    for lag in [1, 7, 14, 28]:
        df[f"lag_{lag}"] = df.groupby(["store_id", "sku_id"])["quantity_sold"].shift(lag)

    # Rolling statistics
    for window in [7, 14, 30]:
        df[f"rolling_mean_{window}"] = (
            df.groupby(["store_id", "sku_id"])["quantity_sold"]
            .transform(lambda x: x.rolling(window, min_periods=1).mean())
        )
        df[f"rolling_std_{window}"] = (
            df.groupby(["store_id", "sku_id"])["quantity_sold"]
            .transform(lambda x: x.rolling(window, min_periods=1).std())
        )

    # Merge weather data
    if not weather_df.empty:
        weather_df["date"] = pd.to_datetime(weather_df["date"])
        weather_cols = [
            "date", "store_id", "temperature_c", "precipitation_mm",
            "humidity_pct", "is_holiday",
        ]
        # Include event columns if present (CHANGE 7)
        for ecol in ["is_local_event", "event_type", "event_magnitude"]:
            if ecol in weather_df.columns:
                weather_cols.append(ecol)
        weather_subset = weather_df[weather_cols].drop_duplicates(subset=["date", "store_id"])
        df = df.merge(weather_subset, on=["date", "store_id"], how="left")

        # One-hot encode event_type for use as regressors (CHANGE 7)
        if "event_type" in df.columns:
            event_dummies = pd.get_dummies(df["event_type"], prefix="evt").astype(int)
            df = pd.concat([df, event_dummies], axis=1)

    # Fill NaN values
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df


def prepare_prophet_data(df: pd.DataFrame, sku_id: str, store_id: str) -> pd.DataFrame:
    """
    Prepare data in Prophet format (ds, y + regressors) for a specific SKU and store.
    """
    mask = (df["sku_id"] == sku_id) & (df["store_id"] == store_id)
    subset = df[mask].copy()

    if subset.empty:
        return pd.DataFrame(columns=["ds", "y"])

    # Aggregate daily
    daily = subset.groupby("date").agg({
        "quantity_sold": "sum",
        "promotion_flag": "max",
    }).reset_index()

    daily.columns = ["ds", "y", "promotion"]

    # Add regressors if available
    if "temperature_c" in subset.columns:
        temp = subset.groupby("date")["temperature_c"].first().reset_index()
        temp.columns = ["ds", "temperature"]
        daily = daily.merge(temp, on="ds", how="left")
        daily["temperature"] = daily["temperature"].fillna(daily["temperature"].median())

    if "is_holiday" in subset.columns:
        hol = subset.groupby("date")["is_holiday"].max().reset_index()
        hol.columns = ["ds", "holiday_flag"]
        daily = daily.merge(hol, on="ds", how="left")
        daily["holiday_flag"] = daily["holiday_flag"].fillna(0)

    # Event regressors (CHANGE 7)
    if "is_local_event" in subset.columns:
        evt = subset.groupby("date")["is_local_event"].max().reset_index()
        evt.columns = ["ds", "is_local_event"]
        daily = daily.merge(evt, on="ds", how="left")
        daily["is_local_event"] = daily["is_local_event"].fillna(0)

    if "event_magnitude" in subset.columns:
        mag = subset.groupby("date")["event_magnitude"].max().reset_index()
        mag.columns = ["ds", "event_magnitude"]
        daily = daily.merge(mag, on="ds", how="left")
        daily["event_magnitude"] = daily["event_magnitude"].fillna(0)

    return daily.sort_values("ds").reset_index(drop=True)


if __name__ == "__main__":
    print("Testing feature engineering...")
    pos_df = load_pos_data()
    weather_df = load_weather_data()

    if not pos_df.empty:
        featured = engineer_features(pos_df, weather_df)
        print(f"  ✓ Features: {featured.shape[1]} columns, {len(featured):,} rows")
        print(f"  Columns: {list(featured.columns)}")

        prophet_data = prepare_prophet_data(featured, "SKU001", "STORE01")
        print(f"  ✓ Prophet data for SKU001/STORE01: {len(prophet_data)} rows")
    else:
        print("  ⚠ No POS data found. Run seed_data.py first.")
