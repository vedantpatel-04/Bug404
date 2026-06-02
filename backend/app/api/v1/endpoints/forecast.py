"""
Forecast endpoints — wraps existing DemandForecaster + festival annotations.
"""
import sys
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.schemas.schemas import (
    ForecastResponse, ForecastPoint, FestivalAnnotation, FestivalPreviewResponse,
)
from backend.app.services.cache import cache

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

router = APIRouter()

# Indian event data (surfaced prominently per product strategy)
INDIAN_EVENTS = [
    {"event_name": "Navratri", "event_type": "festival", "magnitude": 3,
     "categories": ["Snacks", "Dairy", "Beverages"], "typical_lift_pct": 35},
    {"event_name": "Diwali", "event_type": "festival", "magnitude": 3,
     "categories": ["Snacks", "Dairy", "Bakery", "Household"], "typical_lift_pct": 50},
    {"event_name": "Uttarayan", "event_type": "festival", "magnitude": 2,
     "categories": ["Snacks", "Dairy"], "typical_lift_pct": 25},
    {"event_name": "IPL Season", "event_type": "cricket", "magnitude": 2,
     "categories": ["Beverages", "Snacks", "Frozen Foods"], "typical_lift_pct": 20},
    {"event_name": "Holi", "event_type": "festival", "magnitude": 3,
     "categories": ["Dairy", "Snacks", "Beverages"], "typical_lift_pct": 30},
    {"event_name": "Eid-ul-Fitr", "event_type": "festival", "magnitude": 2,
     "categories": ["Snacks", "Dairy", "Bakery"], "typical_lift_pct": 25},
    {"event_name": "Pongal", "event_type": "festival", "magnitude": 2,
     "categories": ["Dairy", "Cereals"], "typical_lift_pct": 20},
    {"event_name": "Janmashtami", "event_type": "festival", "magnitude": 2,
     "categories": ["Dairy"], "typical_lift_pct": 15},
    {"event_name": "Big Billion Day", "event_type": "sale_event", "magnitude": 2,
     "categories": ["Personal Care", "Household", "Snacks"], "typical_lift_pct": 40},
    {"event_name": "Republic Day", "event_type": "holiday", "magnitude": 2,
     "categories": ["Beverages", "Snacks"], "typical_lift_pct": 10},
]


@router.get("/{sku_id}", response_model=ForecastResponse)
async def get_forecast(
    sku_id: str,
    store_id: str = Query(default="STORE01"),
    horizon_days: int = Query(default=30, ge=7, le=90),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get Prophet forecast for a SKU at a store.

    Includes festival spike annotations for Indian events.
    """
    # Check cache
    cache_key = cache.forecast_key(sku_id, store_id)
    cached = await cache.get(cache_key)
    if cached:
        return json.loads(cached)

    try:
        import io

        # The existing DemandForecaster prints Unicode emoji during init
        # which crashes on Windows cp1252. Redirect stdout temporarily.
        old_stdout = sys.stdout
        sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
        try:
            from forecasting.demand_forecaster import DemandForecaster
            forecaster = DemandForecaster()
        finally:
            sys.stdout = old_stdout

        df = forecaster.simulate_forecast_results(sku_id, store_id, days=60 + horizon_days)

        data_points = []
        for _, row in df.iterrows():
            data_points.append(ForecastPoint(
                date=row["ds"].strftime("%Y-%m-%d"),
                yhat=round(row["yhat"], 1),
                yhat_lower=round(row["yhat_lower"], 1),
                yhat_upper=round(row["yhat_upper"], 1),
                actual=round(row.get("actual", 0), 1) if "actual" in row else None,
                is_forecast=bool(row.get("is_forecast", 0)),
            ))

        # Calculate accuracy on historical portion
        actual = df[df["is_forecast"] == 0]["actual"] if "actual" in df.columns else None
        predicted = df[df["is_forecast"] == 0]["yhat"] if "actual" in df.columns else None
        accuracy = None
        if actual is not None and len(actual) > 0:
            accuracy = forecaster.calculate_accuracy(actual, predicted)

        # Add festival annotations
        annotations = _get_festival_annotations()

        result = ForecastResponse(
            sku_id=sku_id,
            store_id=store_id,
            data=data_points,
            accuracy=accuracy,
            festival_annotations=annotations,
        )

        # Cache for 1 hour
        await cache.set(cache_key, result.model_dump_json(), ttl=cache.TTL_FORECAST)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast error: {str(e)}")


@router.get("/festival-preview/{event_name}", response_model=FestivalPreviewResponse)
async def get_festival_preview(
    event_name: str,
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get demand spike preview for a named Indian event.

    Shows predicted demand lift per affected SKU category.
    """
    event = next((e for e in INDIAN_EVENTS if e["event_name"].lower() == event_name.lower()), None)
    if not event:
        raise HTTPException(status_code=404, detail=f"Event '{event_name}' not found")

    # Simulate per-SKU impact data
    import numpy as np
    np.random.seed(hash(event_name) % 2**31)

    sku_impacts = []
    try:
        from database.db_manager import db as legacy_db
        products = legacy_db.get_products()
    except Exception:
        products = [{"sku_id": f"SKU{i:03d}", "product_name": f"Product {i}", "category": "Snacks"}
                     for i in range(1, 11)]

    for p in products[:15]:
        if p.get("category", "") in event["categories"]:
            lift = event["typical_lift_pct"] * np.random.uniform(0.7, 1.3)
            sku_impacts.append({
                "sku_id": p["sku_id"],
                "product_name": p.get("product_name", ""),
                "category": p.get("category", ""),
                "predicted_lift_pct": round(lift, 1),
                "current_stock": int(np.random.randint(5, 80)),
                "risk_level": "red" if lift > 30 else "amber" if lift > 15 else "green",
            })

    return FestivalPreviewResponse(
        event_name=event["event_name"],
        event_type=event["event_type"],
        start_date="2026-10-01",  # Placeholder
        end_date="2026-10-09",
        magnitude=event["magnitude"],
        demand_categories=event["categories"],
        sku_impacts=sku_impacts,
    )


def _get_festival_annotations() -> list[FestivalAnnotation]:
    """Generate festival annotations for the forecast chart."""
    annotations = []
    for event in INDIAN_EVENTS[:6]:
        annotations.append(FestivalAnnotation(
            event_name=event["event_name"],
            event_type=event["event_type"],
            start_date="2026-10-01",
            end_date="2026-10-09",
            magnitude=event["magnitude"],
            predicted_lift_pct=event["typical_lift_pct"],
            demand_categories=event["categories"],
        ))
    return annotations
