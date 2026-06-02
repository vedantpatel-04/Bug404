"""
ShelfIQ Backend — SQLAlchemy ORM Models.

Maps the full database schema from readme2.md Part 5, plus the existing
tables from the SQLite prototype. All India-specific additions included.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Index, Integer,
    LargeBinary, SmallInteger, String, Text,
)
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return str(uuid.uuid4())


# ── Multi-Tenant ─────────────────────────────────────────────

class Organization(Base):
    """One organization = one retail chain."""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=True, comment="GST Identification Number")
    state_code = Column(String(2), nullable=True, comment="Indian state code")
    plan = Column(String(20), default="starter")
    plan_expires = Column(DateTime(timezone=True), nullable=True)
    razorpay_sub_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relationships
    stores = relationship("Store", back_populates="organization")
    users = relationship("User", back_populates="organization")


class User(Base):
    """Platform user (store owners, managers, associates, analysts)."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="SHELF_ASSOCIATE")
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    language = Column(String(5), default="en")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    organization = relationship("Organization", back_populates="users")


# ── Store ────────────────────────────────────────────────────

class Store(Base):
    """Physical store location."""
    __tablename__ = "v3_stores"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=True)
    store_id_legacy = Column(String(20), nullable=True, comment="Maps to existing STORE01/02/03")
    name = Column(String(255), nullable=False)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(6), nullable=True)
    address = Column(Text, nullable=True)
    num_aisles = Column(Integer, default=6)
    shelves_per_aisle = Column(Integer, default=4)
    sections_per_shelf = Column(Integer, default=5)
    timezone = Column(String(50), default="Asia/Kolkata")
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    organization = relationship("Organization", back_populates="stores")
    cameras = relationship("Camera", back_populates="store")
    associates = relationship("Associate", back_populates="store")


# ── Camera ───────────────────────────────────────────────────

class Camera(Base):
    """IP/CCTV camera registered to a store, mapped to an aisle."""
    __tablename__ = "cameras"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    store_id = Column(String(36), ForeignKey("v3_stores.id"), nullable=False)
    name = Column(String(100), nullable=True, comment="e.g. 'Dairy Aisle Cam 1'")
    rtsp_url_enc = Column(LargeBinary, nullable=True, comment="AES-256 encrypted RTSP URL")
    aisle = Column(String(50), nullable=True)
    status = Column(String(20), default="active")
    last_frame_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    store = relationship("Store", back_populates="cameras")


# ── Associate ────────────────────────────────────────────────

class Associate(Base):
    """Store associate with WhatsApp contact for alerts."""
    __tablename__ = "associates"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    store_id = Column(String(36), ForeignKey("v3_stores.id"), nullable=False)
    name = Column(String(100), nullable=False)
    whatsapp_enc = Column(LargeBinary, nullable=True, comment="AES-256 encrypted phone number")
    language = Column(String(5), default="en", comment="en | hi | gu")
    role = Column(String(30), default="SHELF_ASSOCIATE")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    store = relationship("Store", back_populates="associates")


# ── Indian Events ────────────────────────────────────────────

class IndianEvent(Base):
    """Indian festival/event calendar for demand forecasting."""
    __tablename__ = "indian_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_name = Column(String(100), nullable=False)
    event_type = Column(String(30), nullable=True, comment="festival|holiday|cricket|sale_event")
    start_date = Column(String(10), nullable=False, comment="YYYY-MM-DD")
    end_date = Column(String(10), nullable=False)
    magnitude = Column(SmallInteger, nullable=True, comment="1=local, 2=city, 3=national")
    affected_states = Column(Text, nullable=True, comment="Comma-separated state codes, NULL=nationwide")
    demand_categories = Column(Text, nullable=True, comment="Comma-separated SKU categories")
    created_at = Column(DateTime(timezone=True), default=_utcnow)


# ── Festival Stock Risk ──────────────────────────────────────

class FestivalStockRisk(Base):
    """Per-SKU risk assessment for upcoming festivals."""
    __tablename__ = "festival_stock_risk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    store_id = Column(String(36), ForeignKey("v3_stores.id"), nullable=False)
    sku_id = Column(String(50), nullable=False)
    event_id = Column(Integer, ForeignKey("indian_events.id"), nullable=True)
    assessed_at = Column(DateTime(timezone=True), default=_utcnow)
    predicted_lift_pct = Column(Float, nullable=True)
    current_stock = Column(Integer, nullable=True)
    days_to_event = Column(SmallInteger, nullable=True)
    risk_level = Column(String(10), nullable=True, comment="green | amber | red")
    reorder_placed = Column(Boolean, default=False)


# ── Audit Log ────────────────────────────────────────────────

class AuditLog(Base):
    """Append-only audit trail. Never delete or update rows."""
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_audit_user", "user_id", "created_at"),
    )
