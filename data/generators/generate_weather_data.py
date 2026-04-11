"""
Generate synthetic weather and local event data for demand forecast enrichment.
Covers the same 2-year period as POS data for all store locations.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config.settings import POS_HISTORY_DAYS, POS_DATA_DIR

np.random.seed(42)

WEATHER_CONDITIONS = ["Sunny", "Cloudy", "Rainy", "Stormy", "Snowy", "Foggy", "Windy", "Clear"]
LOCAL_EVENTS = [
    "", "", "", "", "", "", "", "",  # Most days have no event
    "Local Festival", "Sports Game", "Concert", "Market Day",
    "Community Fair", "Food Festival", "Marathon", "Parade",
]

US_HOLIDAYS = {
    (1, 1): "New Year's Day",
    (2, 14): "Valentine's Day",
    (7, 4): "Independence Day",
    (10, 31): "Halloween",
    (11, 25): "Thanksgiving (approx)",
    (11, 26): "Black Friday",
    (12, 24): "Christmas Eve",
    (12, 25): "Christmas Day",
    (12, 31): "New Year's Eve",
}


def generate_weather_data() -> pd.DataFrame:
    """Generate synthetic weather and event data."""
    print("Generating weather & event data...")
    store_ids = ["STORE01", "STORE02", "STORE03"]
    end_date = datetime(2026, 4, 1)
    start_date = end_date - timedelta(days=POS_HISTORY_DAYS)
    dates = pd.date_range(start=start_date, end=end_date, freq="D")

    records = []
    for store_id in store_ids:
        # Each store has slightly different climate
        base_temp_offset = np.random.uniform(-3, 3)
        precip_factor = np.random.uniform(0.7, 1.3)

        for date in dates:
            month = date.month
            day = date.day

            # Temperature: seasonal pattern + daily noise
            seasonal_temp = 15 + 15 * np.sin(2 * np.pi * (month - 4) / 12)
            temp = seasonal_temp + base_temp_offset + np.random.normal(0, 4)
            temp = round(temp, 1)

            # Precipitation: higher in winter/spring
            precip_base = max(0, 5 + 10 * np.sin(2 * np.pi * (month - 1) / 12))
            precip = max(0, precip_base * precip_factor + np.random.exponential(2))
            precip = round(precip, 1) if np.random.random() < 0.35 else 0.0

            # Humidity
            humidity = min(100, max(20, 55 + 20 * np.sin(2 * np.pi * (month - 7) / 12) + np.random.normal(0, 10)))
            humidity = round(humidity, 1)

            # Weather condition based on temp and precipitation
            if precip > 15:
                condition = "Stormy"
            elif precip > 5:
                condition = "Rainy"
            elif temp < 0:
                condition = "Snowy" if precip > 0 else "Clear"
            elif precip > 0:
                condition = "Rainy"
            elif humidity > 80:
                condition = "Foggy"
            else:
                condition = np.random.choice(["Sunny", "Cloudy", "Clear", "Windy"], p=[0.4, 0.3, 0.2, 0.1])

            # Holiday
            is_holiday = 1 if (month, day) in US_HOLIDAYS else 0
            holiday_name = US_HOLIDAYS.get((month, day), "")

            # Local event (random, ~5% of days)
            event = np.random.choice(LOCAL_EVENTS)

            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "store_id": store_id,
                "temperature_c": temp,
                "precipitation_mm": precip,
                "humidity_pct": humidity,
                "weather_condition": condition,
                "is_holiday": is_holiday,
                "local_event": event or holiday_name,
            })

    df = pd.DataFrame(records)
    output_path = POS_DATA_DIR / "weather_data.csv"
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved {len(df):,} weather records to {output_path}")
    return df


if __name__ == "__main__":
    generate_weather_data()
