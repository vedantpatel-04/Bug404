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

WEATHER_CONDITIONS = ["Sunny", "Cloudy", "Rainy", "Stormy", "Foggy", "Windy", "Clear", "Haze"]

# ── Ahmedabad / India event calendar (CHANGE 7) ─────────────────
# event_type: festival | holiday | cricket_match | concert | sale_event
# event_magnitude: 1=local, 2=city-wide, 3=major/national
AHMEDABAD_EVENTS = {
    # Uttarayan (Makar Sankranti) — major kite festival
    (1, 14): ("Uttarayan (Makar Sankranti)", "festival", 3),
    (1, 15): ("Uttarayan Day 2", "festival", 3),
    # Republic Day
    (1, 26): ("Republic Day", "holiday", 3),
    # Holi
    (3, 14): ("Holi", "festival", 3),
    (3, 15): ("Holi (Dhuleti)", "festival", 2),
    # IPL season (April–May, simulated key match days)
    (4, 5):  ("IPL Match — Home Game", "cricket_match", 2),
    (4, 12): ("IPL Match — Rivalry", "cricket_match", 3),
    (4, 19): ("IPL Match", "cricket_match", 2),
    (4, 26): ("IPL Match — Home Game", "cricket_match", 2),
    (5, 3):  ("IPL Match", "cricket_match", 2),
    (5, 10): ("IPL Match — Playoff", "cricket_match", 3),
    (5, 17): ("IPL Match", "cricket_match", 2),
    (5, 24): ("IPL Final (if qualified)", "cricket_match", 3),
    # Independence Day
    (8, 15): ("Independence Day", "holiday", 3),
    # Janmashtami
    (8, 26): ("Janmashtami", "festival", 2),
    # Ganesh Chaturthi
    (9, 7):  ("Ganesh Chaturthi", "festival", 2),
    # Navratri (9 nights, Oct) — huge in Gujarat
    (10, 3):  ("Navratri Day 1", "festival", 3),
    (10, 4):  ("Navratri Day 2", "festival", 3),
    (10, 5):  ("Navratri Day 3", "festival", 3),
    (10, 6):  ("Navratri Day 4", "festival", 3),
    (10, 7):  ("Navratri Day 5", "festival", 3),
    (10, 8):  ("Navratri Day 6", "festival", 3),
    (10, 9):  ("Navratri Day 7", "festival", 3),
    (10, 10): ("Navratri Day 8", "festival", 3),
    (10, 11): ("Navratri Day 9 (Maha Navami)", "festival", 3),
    (10, 12): ("Dussehra", "festival", 3),
    # Diwali
    (11, 1):  ("Diwali", "festival", 3),
    (11, 2):  ("Diwali (Govardhan Puja)", "festival", 3),
    (11, 3):  ("Bhai Dooj", "festival", 2),
    # Sale events
    (1, 10):  ("New Year Sale", "sale_event", 2),
    (6, 15):  ("Summer Sale", "sale_event", 2),
    (7, 1):   ("Monsoon Clearance", "sale_event", 1),
    (8, 10):  ("Freedom Sale", "sale_event", 2),
    (10, 1):  ("Festive Season Sale", "sale_event", 3),
    (12, 20): ("Year-End Sale", "sale_event", 2),
    (12, 25): ("Christmas Sale", "sale_event", 1),
    # Concerts / local events
    (2, 14):  ("Valentine's Concert", "concert", 1),
    (3, 8):   ("Ahmedabad Food Festival", "sale_event", 1),
    (11, 15): ("Sabarmati Festival", "concert", 2),
    (12, 31): ("New Year's Eve Concert", "concert", 2),
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

            # ── Event lookup (Ahmedabad calendar) (CHANGE 7) ────────
            event_data = AHMEDABAD_EVENTS.get((month, day), None)
            if event_data:
                event_name, event_type, event_magnitude = event_data
                is_local_event = 1
                is_holiday = 1 if event_type in ("holiday", "festival") else 0
            else:
                event_name = ""
                event_type = ""
                event_magnitude = 0
                is_local_event = 0
                is_holiday = 0

            records.append({
                "date": date.strftime("%Y-%m-%d"),
                "store_id": store_id,
                "temperature_c": temp,
                "precipitation_mm": precip,
                "humidity_pct": humidity,
                "weather_condition": condition,
                "is_holiday": is_holiday,
                "local_event": event_name,
                "is_local_event": is_local_event,       # CHANGE 7
                "event_type": event_type,                # CHANGE 7
                "event_magnitude": event_magnitude,      # CHANGE 7
            })

    df = pd.DataFrame(records)
    output_path = POS_DATA_DIR / "weather_data.csv"
    df.to_csv(output_path, index=False)
    print(f"  ✓ Saved {len(df):,} weather records to {output_path}")
    return df


if __name__ == "__main__":
    generate_weather_data()
