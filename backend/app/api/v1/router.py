"""
ShelfIQ Backend — API v1 Router.

Aggregates all endpoint sub-routers into a single v1 API router.
"""
from fastapi import APIRouter

from backend.app.api.v1.endpoints import (
    auth,
    stores,
    shelves,
    alerts,
    analysis,
    forecast,
    compliance,
    analytics,
    events,
    webhooks,
    billing,
    quick_commerce,
)

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(stores.router, prefix="/stores", tags=["Stores"])
api_router.include_router(shelves.router, prefix="/shelves", tags=["Shelves"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["Forecast"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(events.router, prefix="/events", tags=["Events"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(quick_commerce.router, prefix="/qcommerce", tags=["Quick Commerce"])

