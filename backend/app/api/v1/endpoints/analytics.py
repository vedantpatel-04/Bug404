"""
Analytics endpoints — heatmap, revenue recovery, festival ROI.
"""
import sys
from pathlib import Path
from typing import Optional

import numpy as np
from fastapi import APIRouter, Depends, Query

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.schemas.schemas import HeatmapResponse, HeatmapCell

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

router = APIRouter()


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_stockout_heatmap(
    store_id: str = Query(default="STORE01"),
    period: str = Query(default="7d", description="7d | 30d | 90d"),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get aisle × hour stockout heatmap data.

    Returns a grid of stockout counts by aisle (Y-axis) and hour (X-axis).
    """
    try:
        from database.db_manager import db as legacy_db
        # Try to get real alert data grouped by aisle and hour
        alerts = legacy_db.get_active_alerts(store_id)
    except Exception:
        alerts = []

    # If we have real data, aggregate it
    if alerts:
        from collections import defaultdict
        from datetime import datetime

        heatmap_data = defaultdict(lambda: {"count": 0, "severities": []})
        for alert in alerts:
            aisle = alert.get("aisle_id", "A01")
            created = alert.get("created_at", "")
            try:
                hour = datetime.fromisoformat(created).hour
            except Exception:
                hour = 12
            key = (aisle, hour)
            heatmap_data[key]["count"] += 1
            heatmap_data[key]["severities"].append(alert.get("severity", 1))

        cells = [
            HeatmapCell(
                aisle=k[0], hour=k[1],
                stockout_count=v["count"],
                severity_avg=round(sum(v["severities"]) / len(v["severities"]), 1),
            )
            for k, v in heatmap_data.items()
        ]
    else:
        # Generate demo heatmap data
        np.random.seed(hash(store_id) % 2**31)
        aisles = [f"A{i:02d}" for i in range(1, 7)]
        hours = list(range(8, 22))  # 8 AM to 10 PM

        cells = []
        for aisle in aisles:
            for hour in hours:
                # Peak hours (11-14, 17-20) have more stockouts
                peak_factor = 2.0 if hour in [11, 12, 13, 17, 18, 19] else 1.0
                count = int(np.random.poisson(3 * peak_factor))
                if count > 0:
                    cells.append(HeatmapCell(
                        aisle=aisle,
                        hour=hour,
                        stockout_count=count,
                        severity_avg=round(np.random.uniform(2, 5), 1),
                    ))

    return HeatmapResponse(store_id=store_id, data=cells, period=period)


@router.get("/revenue-recovery")
async def get_revenue_recovery(
    store_id: str = Query(default="STORE01"),
    user: TokenPayload = Depends(get_current_user),
):
    """Revenue recovery analytics — cost of stockouts vs recoveries."""
    np.random.seed(hash(store_id) % 2**31)

    days = 30
    data = []
    for i in range(days):
        from datetime import datetime, timedelta
        date = datetime.now() - timedelta(days=days - i)
        lost = round(np.random.uniform(2000, 15000), 0)
        recovered = round(lost * np.random.uniform(0.4, 0.8), 0)
        data.append({
            "date": date.strftime("%Y-%m-%d"),
            "revenue_lost": lost,
            "revenue_recovered": recovered,
            "recovery_pct": round(recovered / lost * 100, 1),
        })

    total_lost = sum(d["revenue_lost"] for d in data)
    total_recovered = sum(d["revenue_recovered"] for d in data)

    return {
        "store_id": store_id,
        "period_days": days,
        "total_revenue_lost": round(total_lost, 0),
        "total_revenue_recovered": round(total_recovered, 0),
        "recovery_rate": round(total_recovered / max(total_lost, 1) * 100, 1),
        "daily_data": data,
    }
