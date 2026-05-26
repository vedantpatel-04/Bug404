"""
ShelfIQ Edge — Sync Daemon.

Runs on Raspberry Pi 5 / Jetson Nano for stores with unreliable internet.
- Performs YOLOv8 inference on local camera streams
- Queues results in a local SQLite buffer
- Syncs to ShelfIQ cloud when connectivity returns
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import httpx

# Configuration
CLOUD_URL = os.getenv("SHELFIQ_CLOUD_URL", "https://api.shelfiq.in")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_SECONDS", "300"))  # 5 minutes
STORE_ID = os.getenv("STORE_ID", "STORE01")
API_TOKEN = os.getenv("SHELFIQ_API_TOKEN", "")
LOCAL_DB = Path("edge_buffer.db")

# Add project modules to path
sys.path.insert(0, str(Path(__file__).parent))


def init_local_db():
    """Create local buffer database."""
    conn = sqlite3.connect(str(LOCAL_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            synced INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


def run_inference():
    """Run shelf analysis on local camera feeds."""
    try:
        from pipeline.shelf_analysis_pipeline import ShelfAnalysisPipeline

        pipeline = ShelfAnalysisPipeline()
        results = pipeline.analyze_store(STORE_ID)

        # Buffer results locally
        conn = sqlite3.connect(str(LOCAL_DB))
        for result in results:
            payload = json.dumps({
                "store_id": result.store_id,
                "aisle_id": result.aisle_id,
                "num_detections": result.num_detections,
                "shelf_health_score": result.shelf_health_score,
                "stock_levels": result.stock_levels,
                "alerts": result.alerts,
                "timestamp": result.timestamp,
            }, default=str)

            conn.execute(
                "INSERT INTO pending_results (store_id, payload, created_at) VALUES (?, ?, ?)",
                (STORE_ID, payload, datetime.now().isoformat()),
            )
        conn.commit()
        conn.close()

        print(f"  ✓ Inference complete: {len(results)} cameras, buffered locally")
        return len(results)

    except Exception as e:
        print(f"  ⚠ Inference error: {e}")
        return 0


def sync_to_cloud():
    """Upload buffered results to ShelfIQ cloud."""
    if not API_TOKEN:
        print("  ℹ No API token configured — skipping cloud sync")
        return

    conn = sqlite3.connect(str(LOCAL_DB))
    conn.row_factory = sqlite3.Row
    pending = conn.execute(
        "SELECT * FROM pending_results WHERE synced = 0 ORDER BY created_at ASC LIMIT 50"
    ).fetchall()

    if not pending:
        print("  ℹ No pending results to sync")
        return

    print(f"  ↑ Syncing {len(pending)} results to cloud...")
    synced_ids = []

    try:
        with httpx.Client(timeout=30.0) as client:
            for row in pending:
                try:
                    response = client.post(
                        f"{CLOUD_URL}/api/v1/analysis/sync",
                        json=json.loads(row["payload"]),
                        headers={"Authorization": f"Bearer {API_TOKEN}"},
                    )
                    if response.status_code in (200, 201):
                        synced_ids.append(row["id"])
                except httpx.ConnectError:
                    print("  ⚠ Cloud unreachable — will retry next cycle")
                    break
                except Exception as e:
                    print(f"  ⚠ Sync error for result {row['id']}: {e}")

    except Exception as e:
        print(f"  ⚠ Cloud connection error: {e}")

    # Mark synced
    if synced_ids:
        placeholders = ",".join("?" * len(synced_ids))
        conn.execute(f"UPDATE pending_results SET synced = 1 WHERE id IN ({placeholders})", synced_ids)
        conn.commit()
        print(f"  ✓ Synced {len(synced_ids)}/{len(pending)} results")

    conn.close()


def main():
    """Main loop: inference → buffer → sync → repeat."""
    print("=" * 60)
    print("  🛒 ShelfIQ Edge AI Daemon")
    print(f"  Store: {STORE_ID}")
    print(f"  Cloud: {CLOUD_URL}")
    print(f"  Sync interval: {SYNC_INTERVAL}s")
    print("=" * 60)

    init_local_db()

    while True:
        print(f"\n  [{datetime.now().strftime('%H:%M:%S')}] Running cycle...")

        # Step 1: Run inference
        run_inference()

        # Step 2: Try to sync
        sync_to_cloud()

        # Step 3: Wait
        print(f"  ⏱ Next cycle in {SYNC_INTERVAL}s")
        time.sleep(SYNC_INTERVAL)


if __name__ == "__main__":
    main()
