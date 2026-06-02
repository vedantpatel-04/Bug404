"""
Shelf state endpoints — wraps existing CV detection data.
"""
import sys
from pathlib import Path

from fastapi import APIRouter, Depends

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.schemas.schemas import ShelfStateResponse, ShelfSection
from backend.app.services.cache import cache

# Add project root to path so we can import existing modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

router = APIRouter()


@router.get("/{store_id}", response_model=list[ShelfStateResponse])
async def get_shelf_states(
    store_id: str,
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get current shelf states + stock levels for a store.

    Wraps the existing database detections and stock classifications.
    """
    # Check cache first
    cached = await cache.get(cache.shelf_key(store_id))
    if cached:
        import json
        return json.loads(cached)

    # Import existing database manager
    try:
        from database.db_manager import db as legacy_db
        detections = legacy_db.get_recent_detections(store_id, limit=200)
    except Exception:
        detections = []

    # Group by aisle
    aisles: dict[str, list] = {}
    for det in detections:
        aisle = det.get("aisle_id", "A01")
        if aisle not in aisles:
            aisles[aisle] = []
        aisles[aisle].append(det)

    results = []
    for aisle_id, dets in aisles.items():
        sections = []
        for det in dets:
            sections.append(ShelfSection(
                section_id=det.get("shelf_id", ""),
                stock_level=det.get("stock_level", "FULL"),
                fill_ratio=det.get("confidence", 1.0),
                detected=int(det.get("confidence", 1.0) * 4),
                expected=4,
                sku_id=det.get("sku_id"),
            ))

        # Calculate health score
        full_count = sum(1 for s in sections if s.stock_level == "FULL")
        health = (full_count / max(len(sections), 1)) * 100

        results.append(ShelfStateResponse(
            store_id=store_id,
            aisle_id=aisle_id,
            sections=sections,
            health_score=round(health, 1),
            last_updated=dets[0].get("detected_at") if dets else None,
        ))

    # Cache for 30 seconds
    if results:
        import json
        await cache.set(
            cache.shelf_key(store_id),
            json.dumps([r.model_dump() for r in results], default=str),
            ttl=cache.TTL_SHELF_STATE,
        )

    return results
