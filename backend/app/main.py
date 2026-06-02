"""
ShelfIQ v3.0 — FastAPI Application Entry Point.

India's first shelf intelligence platform.
Wraps existing ML modules and exposes them as a modern REST + WebSocket API.
"""
import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path so existing modules (models/, forecasting/, etc.) are importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))  # noqa: E402

from backend.app.core.config import settings  # noqa: E402
from backend.app.db.database import init_db, close_db  # noqa: E402
from backend.app.services.cache import cache  # noqa: E402
from backend.app.schemas.schemas import HealthResponse  # noqa: E402


# ── Lifespan ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle hooks."""
    # Startup
    print(f"  [ShelfIQ] v{settings.APP_VERSION} starting...")
    print(f"  [ENV] {settings.ENVIRONMENT}")
    print(f"  [DB] {'SQLite' if settings.is_sqlite else 'PostgreSQL'}")

    # Initialize database tables
    await init_db()
    print("  [OK] Database initialized")

    # Connect Redis cache
    await cache.connect()
    print(f"  [OK] Cache: {cache.status}")

    # Verify existing ML modules are importable
    ml_status = _check_ml_modules()
    print(f"  [OK] ML Modules: {ml_status}")

    yield

    # Shutdown
    await cache.close()
    await close_db()
    print("  [ShelfIQ] Shutdown complete.")


# ── App Creation ─────────────────────────────────────────────

app = FastAPI(
    title="ShelfIQ API",
    description=(
        "India's first shelf intelligence platform — "
        "CV-driven inventory monitoring with WhatsApp alerts, "
        "Indian festival demand forecasting, and planogram compliance."
    ),
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────

from backend.app.api.v1.router import api_router  # noqa: E402
app.include_router(api_router)


# ── Health Check (public, no auth required) ──────────────────

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint — always public.

    Returns status of: database, Redis, ML models, environment.
    """
    db_status = "connected"
    try:
        from backend.app.db.database import engine
        async with engine.connect() as conn:
            if settings.is_sqlite:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
            else:
                await conn.execute(
                    __import__("sqlalchemy").text("SELECT 1")
                )
    except Exception as e:
        db_status = f"error: {str(e)[:50]}"

    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        db=db_status,
        redis=cache.status,
        ml_models=_check_ml_modules(),
        environment=settings.ENVIRONMENT,
    )


# ── Root ─────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    return {
        "name": "ShelfIQ API",
        "version": settings.APP_VERSION,
        "description": "India's Shelf Intelligence Platform",
        "docs": "/docs",
        "health": "/health",
    }


# ── Helpers ──────────────────────────────────────────────────

def _check_ml_modules() -> str:
    """Check if existing ML modules are importable."""
    available = []
    try:
        import models.shelf_detector
        available.append("YOLOv8")
    except ImportError:
        pass
    try:
        import models.sku_recognizer
        available.append("CLIP")
    except ImportError:
        pass
    try:
        import forecasting.demand_forecaster
        available.append("Prophet")
    except ImportError:
        pass
    try:
        import alerts.alert_manager
        available.append("Alerts")
    except ImportError:
        pass

    if available:
        return f"loaded ({', '.join(available)})"
    return "none loaded (run from project root)"
