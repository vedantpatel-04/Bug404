"""
Alert endpoints — CRUD + WebSocket streaming.

Wraps existing AlertManager and adds v3 features:
- Pagination and filtering
- Resolution tracking with timestamps
- WebSocket real-time streaming
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status

from backend.app.core.security import TokenPayload, get_current_user
from backend.app.schemas.schemas import AlertResponse, AlertResolveRequest, AlertListResponse
from backend.app.notifications.whatsapp import whatsapp

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent))

router = APIRouter()


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    severity: Optional[int] = Query(None, ge=1, le=5),
    alert_type: Optional[str] = Query(None),
    store_id: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: TokenPayload = Depends(get_current_user),
):
    """
    Get paginated alerts with filters.

    Filters: severity, alert_type, store_id, status (active/resolved).
    """
    try:
        from database.db_manager import db as legacy_db
        from alerts.alert_manager import AlertManager

        manager = AlertManager()

        if status_filter == "resolved":
            all_alerts_data = legacy_db.fetch_all(
                "alerts",
                where="acknowledged = 1" + (f" AND store_id = '{store_id}'" if store_id else ""),
                order_by="created_at DESC",
            )
        else:
            all_alerts_data = legacy_db.get_active_alerts(store_id or "")

    except Exception:
        all_alerts_data = []

    # Apply filters
    filtered = all_alerts_data
    if severity:
        filtered = [a for a in filtered if a.get("severity") == severity]
    if alert_type:
        filtered = [a for a in filtered if a.get("alert_type") == alert_type]

    total = len(filtered)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_data = filtered[start:end]

    alerts = [
        AlertResponse(
            alert_id=a.get("alert_id", 0),
            alert_type=a.get("alert_type", ""),
            severity=a.get("severity", 1),
            store_id=a.get("store_id", ""),
            aisle_id=a.get("aisle_id", ""),
            shelf_id=a.get("shelf_id", ""),
            sku_id=a.get("sku_id", ""),
            message=a.get("message", ""),
            revenue_impact=a.get("revenue_impact", 0),
            suggested_action=a.get("suggested_action", ""),
            corrective_action=a.get("corrective_action"),
            priority_score=a.get("priority_score", 0),
            acknowledged=bool(a.get("acknowledged", 0)),
            acknowledged_by=a.get("acknowledged_by"),
            created_at=a.get("created_at", ""),
            acknowledged_at=a.get("acknowledged_at"),
        )
        for a in page_data
    ]

    return AlertListResponse(alerts=alerts, total=total, page=page, page_size=page_size)


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    body: AlertResolveRequest,
    user: TokenPayload = Depends(get_current_user),
):
    """
    Mark an alert as resolved with resolution note and timestamp.
    Records resolution time for KPI tracking.
    """
    try:
        from database.db_manager import db as legacy_db

        # Acknowledge in existing system
        legacy_db.acknowledge_alert(alert_id, user=body.resolved_by or user.sub)

        return {
            "alert_id": alert_id,
            "status": "resolved",
            "resolved_by": body.resolved_by or user.sub,
            "resolved_at": datetime.now().isoformat(),
            "resolution_note": body.resolution_note,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}",
        )


# ── WebSocket for Real-Time Alert Streaming ──────────────────

# Connected WebSocket clients
_ws_clients: list[WebSocket] = []


@router.websocket("/ws")
async def alert_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert streaming.

    Clients connect here to receive live alert updates as they are generated
    by the CV pipeline.
    """
    await websocket.accept()
    _ws_clients.append(websocket)

    try:
        while True:
            # Keep connection alive, listen for client messages
            data = await websocket.receive_text()
            # Clients can send "ping" to keep alive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        _ws_clients.remove(websocket)


async def broadcast_alert(alert_data: dict) -> None:
    """Broadcast an alert to all connected WebSocket clients."""
    message = json.dumps(alert_data, default=str)
    disconnected = []
    for ws in _ws_clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)

    for ws in disconnected:
        _ws_clients.remove(ws)
