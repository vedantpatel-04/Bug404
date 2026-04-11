"""
Periodic job scheduler — runs shelf analysis, forecast refresh, and alert digests.
Uses APScheduler for background task execution.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from datetime import datetime


class SimpleScheduler:
    """
    Simple scheduler for periodic tasks.
    Falls back to a basic loop if APScheduler is not available.
    """

    def __init__(self):
        self.jobs = {}
        self.use_apscheduler = False
        self.scheduler = None

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            self.scheduler = BackgroundScheduler()
            self.use_apscheduler = True
        except ImportError:
            print("  ℹ APScheduler not available — using manual scheduling")

    def add_job(self, func, interval_seconds: int, job_id: str, name: str = ""):
        """Add a periodic job."""
        self.jobs[job_id] = {
            "func": func,
            "interval": interval_seconds,
            "name": name or job_id,
            "last_run": None,
        }

        if self.use_apscheduler and self.scheduler:
            self.scheduler.add_job(
                func,
                "interval",
                seconds=interval_seconds,
                id=job_id,
                name=name,
            )

    def start(self):
        """Start the scheduler."""
        if self.use_apscheduler and self.scheduler:
            self.scheduler.start()
            print("  ✓ APScheduler started")
        else:
            print("  ✓ Manual scheduler ready (call run_once() to execute jobs)")

    def stop(self):
        """Stop the scheduler."""
        if self.use_apscheduler and self.scheduler:
            self.scheduler.shutdown()

    def run_once(self):
        """Run all registered jobs once (for manual mode)."""
        for job_id, job in self.jobs.items():
            try:
                print(f"  ▶ Running: {job['name']}")
                job["func"]()
                job["last_run"] = datetime.now().isoformat()
            except Exception as e:
                print(f"  ⚠ Job {job_id} failed: {e}")

    def get_status(self) -> list:
        """Get status of all jobs."""
        return [
            {
                "job_id": jid,
                "name": j["name"],
                "interval_sec": j["interval"],
                "last_run": j["last_run"],
            }
            for jid, j in self.jobs.items()
        ]


def run_shelf_analysis():
    """Run shelf analysis on latest camera images."""
    try:
        from pipeline.shelf_analysis_pipeline import ShelfAnalysisPipeline
        pipeline = ShelfAnalysisPipeline()
        results = pipeline.analyze_store("STORE01")
        for r in results:
            pipeline.save_results(r)
        print(f"    Analyzed {len(results)} images")
    except Exception as e:
        print(f"    Shelf analysis error: {e}")


def run_forecast_refresh():
    """Refresh demand forecasts for top SKUs."""
    try:
        from forecasting.demand_forecaster import DemandForecaster
        from forecasting.feature_engineering import load_pos_data, load_weather_data, engineer_features, prepare_prophet_data

        forecaster = DemandForecaster()
        pos_df = load_pos_data()
        weather_df = load_weather_data()

        if not pos_df.empty:
            featured = engineer_features(pos_df, weather_df)
            # Forecast top 5 SKUs
            for sku in ["SKU001", "SKU006", "SKU011", "SKU016", "SKU026"]:
                data = prepare_prophet_data(featured, sku, "STORE01")
                if not data.empty:
                    forecast = forecaster.forecast(data, sku, "STORE01", horizon_days=14)
                    print(f"    Forecast generated for {sku}: {len(forecast)} days")
    except Exception as e:
        print(f"    Forecast refresh error: {e}")


def run_alert_digest():
    """Send alert digest notification."""
    try:
        from alerts.alert_manager import AlertManager
        from alerts.notification_channels import notifier

        manager = AlertManager()
        active = manager.get_active_alerts()
        if active:
            notifier.notify_batch(active, channels=["dashboard", "email"])
            print(f"    Digest sent for {len(active)} active alerts")
        else:
            print("    No active alerts")
    except Exception as e:
        print(f"    Alert digest error: {e}")


def create_default_scheduler() -> SimpleScheduler:
    """Create scheduler with default retail jobs."""
    scheduler = SimpleScheduler()
    scheduler.add_job(run_shelf_analysis, 300, "shelf_analysis", "Shelf CV Analysis (5 min)")
    scheduler.add_job(run_forecast_refresh, 86400, "forecast_refresh", "Demand Forecast Refresh (daily)")
    scheduler.add_job(run_alert_digest, 3600, "alert_digest", "Alert Digest (hourly)")
    return scheduler


if __name__ == "__main__":
    print("Running scheduled jobs once...")
    scheduler = create_default_scheduler()
    scheduler.run_once()
    print("Done.")
