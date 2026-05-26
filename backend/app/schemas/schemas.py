"""
ShelfIQ Backend — Pydantic v2 Request/Response Schemas.

All schemas use extra='forbid' to reject unexpected fields.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ── Auth ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=4, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserInfo"


class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str
    role: str
    org_id: Optional[str] = None


# ── Store ────────────────────────────────────────────────────

class StoreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=255)
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, max_length=6)
    address: Optional[str] = None
    num_aisles: int = Field(default=6, ge=1, le=50)
    shelves_per_aisle: int = Field(default=4, ge=1, le=20)
    sections_per_shelf: int = Field(default=5, ge=1, le=20)


class StoreResponse(BaseModel):
    id: str
    name: str
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    num_aisles: int
    shelves_per_aisle: int
    sections_per_shelf: int
    timezone: str
    created_at: Optional[datetime] = None


# ── Camera ───────────────────────────────────────────────────

class CameraCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=100)
    rtsp_url: str = Field(..., min_length=5, description="RTSP stream URL (will be encrypted)")
    aisle: Optional[str] = None


class CameraResponse(BaseModel):
    id: str
    name: str
    aisle: Optional[str] = None
    status: str
    last_frame_at: Optional[datetime] = None
    # NOTE: rtsp_url is NEVER returned to the client


# ── Alert ────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    alert_id: int
    alert_type: str
    severity: int
    store_id: str
    aisle_id: str
    shelf_id: str
    sku_id: str
    message: str
    revenue_impact: float
    suggested_action: str
    corrective_action: Optional[str] = None
    priority_score: float
    acknowledged: bool
    acknowledged_by: Optional[str] = None
    created_at: str
    acknowledged_at: Optional[str] = None
    # v3 extensions
    assigned_to: Optional[str] = None
    whatsapp_sent_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution_time_minutes: Optional[int] = None
    resolution_note: Optional[str] = None


class AlertResolveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resolution_note: str = Field(default="", max_length=500)
    resolved_by: Optional[str] = None


class AlertListResponse(BaseModel):
    alerts: list[AlertResponse]
    total: int
    page: int
    page_size: int


# ── Forecast ─────────────────────────────────────────────────

class ForecastPoint(BaseModel):
    date: str
    yhat: float
    yhat_lower: float
    yhat_upper: float
    actual: Optional[float] = None
    is_forecast: bool = False


class FestivalAnnotation(BaseModel):
    event_name: str
    event_type: str
    start_date: str
    end_date: str
    magnitude: int
    predicted_lift_pct: Optional[float] = None
    demand_categories: Optional[list[str]] = None


class ForecastResponse(BaseModel):
    sku_id: str
    store_id: str
    data: list[ForecastPoint]
    accuracy: Optional[dict] = None
    festival_annotations: list[FestivalAnnotation] = []


class FestivalPreviewResponse(BaseModel):
    event_name: str
    event_type: str
    start_date: str
    end_date: str
    magnitude: int
    demand_categories: list[str]
    sku_impacts: list[dict]


# ── Compliance ───────────────────────────────────────────────

class ComplianceViolation(BaseModel):
    aisle_id: str
    shelf_id: str
    violation_type: str
    sku_id: Optional[str] = None
    details: str


class ComplianceResponse(BaseModel):
    store_id: str
    overall_score: float
    grade: str
    total_sections: int
    correct_sections: int
    violations: list[ComplianceViolation]
    checked_at: Optional[str] = None


# ── Analytics ────────────────────────────────────────────────

class HeatmapCell(BaseModel):
    aisle: str
    hour: int
    stockout_count: int
    severity_avg: float


class HeatmapResponse(BaseModel):
    store_id: str
    data: list[HeatmapCell]
    period: str


# ── Events ───────────────────────────────────────────────────

class EventResponse(BaseModel):
    id: int
    event_name: str
    event_type: str
    start_date: str
    end_date: str
    magnitude: int
    days_until: int
    demand_categories: list[str] = []
    predicted_impact: Optional[str] = None


class UpcomingEventsResponse(BaseModel):
    events: list[EventResponse]
    total: int


# ── Analysis ─────────────────────────────────────────────────

class AnalysisRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    store_id: str
    aisle_id: Optional[str] = None
    image_path: Optional[str] = None


class AnalysisRunResponse(BaseModel):
    job_id: str
    status: str
    message: str


# ── Health ───────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    db: str
    redis: str
    ml_models: str
    environment: str


# ── Shelf State ──────────────────────────────────────────────

class ShelfSection(BaseModel):
    section_id: str
    stock_level: str
    fill_ratio: float
    detected: int
    expected: int
    sku_id: Optional[str] = None


class ShelfStateResponse(BaseModel):
    store_id: str
    aisle_id: str
    sections: list[ShelfSection]
    health_score: float
    last_updated: Optional[str] = None


# ── Associate ────────────────────────────────────────────────

class AssociateCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., min_length=1, max_length=100)
    whatsapp_number: str = Field(..., min_length=10, max_length=15)
    language: str = Field(default="en", pattern="^(en|hi|gu)$")
    role: str = Field(default="SHELF_ASSOCIATE")


class AssociateResponse(BaseModel):
    id: str
    name: str
    whatsapp_masked: str  # Never return full number
    language: str
    role: str
    is_active: bool
