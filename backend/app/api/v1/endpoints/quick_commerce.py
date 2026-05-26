"""
Quick-Commerce endpoints — Blinkit, Zepto, Swiggy Instamart integration.
"""
from fastapi import APIRouter, Depends

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.services.quick_commerce import qcommerce

router = APIRouter()


@router.get("/platforms")
async def list_platforms(
    user: TokenPayload = Depends(get_current_user),
):
    """List supported quick-commerce platforms and connection status."""
    return {"platforms": qcommerce.get_supported_platforms()}


@router.post("/sync")
async def sync_inventory(
    platform: str,
    store_id: str = "STORE01",
    user: TokenPayload = Depends(get_current_user),
):
    """Push current stock levels to a quick-commerce platform."""
    # Get current inventory from legacy DB
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))
        from database.db_manager import db as legacy_db
        detections = legacy_db.get_recent_detections(store_id, limit=50)
        items = [
            {"sku_id": d.get("sku_id", ""), "stock_count": d.get("quantity", 0), "price": d.get("price", 0)}
            for d in detections
        ]
    except Exception:
        # Demo items
        items = [
            {"sku_id": "SKU001", "stock_count": 42, "price": 55},
            {"sku_id": "SKU002", "stock_count": 8, "price": 199},
            {"sku_id": "SKU003", "stock_count": 0, "price": 120},
        ]

    result = await qcommerce.sync_inventory(platform, store_id, items)
    return result


@router.get("/orders")
async def fetch_orders(
    platform: str,
    store_id: str = "STORE01",
    since_hours: int = 24,
    user: TokenPayload = Depends(get_current_user),
):
    """Pull recent orders from a quick-commerce platform."""
    result = await qcommerce.fetch_orders(platform, store_id, since_hours)
    return result
