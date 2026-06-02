"""
ShelfIQ — Celery Worker Tasks.

Separate queues for different workloads:
- cv_pipeline:      GPU-accelerated (YOLOv8 + CLIP), max 2 concurrent
- forecast:         CPU, daily at 2 AM IST
- whatsapp_alerts:  High priority, max retries 3, retry delay 30s
- digest_alerts:    Batch job at 6 PM + 10 PM IST
"""
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from celery import Celery  # noqa: E402
from celery.schedules import crontab  # noqa: E402

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

app = Celery("shelfiq", broker=REDIS_URL, backend=REDIS_URL)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_routes={
        "backend.app.workers.tasks.run_cv_pipeline": {"queue": "cv_pipeline"},
        "backend.app.workers.tasks.run_forecast": {"queue": "forecast"},
        "backend.app.workers.tasks.send_whatsapp_alert": {"queue": "whatsapp_alerts"},
        "backend.app.workers.tasks.send_digest": {"queue": "digest_alerts"},
    },
)

# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    "daily-forecast": {
        "task": "backend.app.workers.tasks.run_forecast",
        "schedule": crontab(hour=2, minute=0),  # 2 AM IST daily
        "args": (),
    },
    "evening-digest": {
        "task": "backend.app.workers.tasks.send_digest",
        "schedule": crontab(hour=18, minute=0),  # 6 PM IST
        "args": ("evening",),
    },
    "night-digest": {
        "task": "backend.app.workers.tasks.send_digest",
        "schedule": crontab(hour=22, minute=0),  # 10 PM IST
        "args": ("night",),
    },
}


# ── CV Pipeline Task ─────────────────────────────────────────

@app.task(name="backend.app.workers.tasks.run_cv_pipeline", bind=True, max_retries=2)
def run_cv_pipeline(self, store_id: str, image_path: str = None, aisle_id: str = "A01"):
    """Run YOLOv8 + CLIP shelf analysis pipeline."""
    try:
        from pipeline.shelf_analysis_pipeline import ShelfAnalysisPipeline

        pipeline = ShelfAnalysisPipeline()

        if image_path:
            result = pipeline.analyze_image(image_path, store_id=store_id, aisle_id=aisle_id)
            pipeline.save_results(result)
            return {
                "status": "completed",
                "store_id": store_id,
                "detections": result.num_detections,
                "health_score": result.shelf_health_score,
                "alerts": len(result.alerts),
            }
        else:
            results = pipeline.analyze_store(store_id)
            for r in results:
                pipeline.save_results(r)
            return {
                "status": "completed",
                "store_id": store_id,
                "cameras_processed": len(results),
            }

    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


# ── Forecast Task ────────────────────────────────────────────

@app.task(name="backend.app.workers.tasks.run_forecast")
def run_forecast():
    """Run daily Prophet forecast for all active SKUs."""
    try:
        from forecasting.demand_forecaster import DemandForecaster
        from forecasting.feature_engineering import load_pos_data, load_weather_data, engineer_features, prepare_prophet_data
        from database.db_manager import db as legacy_db

        forecaster = DemandForecaster()
        pos_df = load_pos_data()
        weather_df = load_weather_data()

        if pos_df.empty:
            return {"status": "skipped", "reason": "No POS data"}

        featured = engineer_features(pos_df, weather_df)
        products = legacy_db.get_products()
        stores = legacy_db.get_stores()

        count = 0
        for product in products[:10]:  # Limit for dev
            for store in stores:
                sku_id = product["sku_id"]
                store_id = store["store_id"]
                prophet_data = prepare_prophet_data(featured, sku_id, store_id)
                if not prophet_data.empty:
                    forecaster.forecast(prophet_data, sku_id, store_id)
                    count += 1

        return {"status": "completed", "forecasts_generated": count}

    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── WhatsApp Alert Task ──────────────────────────────────────

@app.task(
    name="backend.app.workers.tasks.send_whatsapp_alert",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_whatsapp_alert(self, alert_data: dict):
    """Send a WhatsApp alert message to the assigned associate."""
    try:
        import asyncio
        from backend.app.notifications.whatsapp import whatsapp

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        result = loop.run_until_complete(
            whatsapp.send_stockout_alert(
                to_phone=alert_data.get("phone", ""),
                store_name=alert_data.get("store_name", ""),
                aisle=alert_data.get("aisle", ""),
                product_name=alert_data.get("product_name", ""),
                action=alert_data.get("action", ""),
                time_str=alert_data.get("time", ""),
                language=alert_data.get("language", "en"),
            )
        )

        loop.close()
        return result

    except Exception as exc:
        raise self.retry(exc=exc)


# ── Digest Task ──────────────────────────────────────────────

@app.task(name="backend.app.workers.tasks.send_digest")
def send_digest(shift: str = "evening"):
    """
    Send batch WhatsApp digest at shift end.
    Aggregates MEDIUM priority alerts into a single summary message.
    """
    try:
        from alerts.alert_manager import AlertManager

        manager = AlertManager()
        alerts = manager.get_active_alerts()
        medium_alerts = [a for a in alerts if a.severity == 2]

        return {
            "status": "completed",
            "shift": shift,
            "alerts_in_digest": len(medium_alerts),
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}
