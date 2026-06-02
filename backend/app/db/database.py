"""
ShelfIQ Backend — Async Database Engine & Session Management.

Supports:
- PostgreSQL via asyncpg (production)
- SQLite via aiosqlite (development)

Uses SQLAlchemy 2.0 async API.
"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from backend.app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ── Engine Setup ─────────────────────────────────────────────

_engine_kwargs = {}

if settings.is_sqlite:
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "echo": settings.DEBUG,
    }
else:
    _engine_kwargs = {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "echo": settings.DEBUG,
    }

engine = create_async_engine(settings.DATABASE_URL, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Session Dependency ───────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that provides an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── Lifecycle ────────────────────────────────────────────────

async def init_db() -> None:
    """Create all tables. Called during app startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose engine. Called during app shutdown."""
    await engine.dispose()
