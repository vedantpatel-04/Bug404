"""
ShelfIQ Backend — Audit Logging Service.

Every data access event is logged to the audit_log table:
- user, action, resource, IP, timestamp

The audit_log table is append-only. Never delete or update rows.
"""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.models import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    user_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """
    Write an audit log entry.

    Args:
        db: Async database session.
        action: What happened (e.g. "alert.resolve", "store.create", "login.success").
        user_id: Who did it.
        resource_type: What kind of resource (e.g. "alert", "store", "camera").
        resource_id: Which specific resource.
        ip_address: Client IP (hashed or masked in production).
        details: Additional JSON-serializable details.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        details=details,
    )
    db.add(entry)
    # Don't commit here — let the session dependency handle it
