"""
Store & Camera endpoints — CRUD for stores and cameras.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.core.security import TokenPayload, get_current_user, require_role, UserRole
from backend.app.core.encryption import encrypt_field, decrypt_field, mask_phone
from backend.app.db.database import get_db
from backend.app.db.models import Store, Camera, Associate
from backend.app.schemas.schemas import (
    StoreCreate, StoreResponse,
    CameraCreate, CameraResponse,
    AssociateCreate, AssociateResponse,
)
from backend.app.services.audit import log_action

router = APIRouter()


# ── Stores ───────────────────────────────────────────────────

@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    body: StoreCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role(UserRole.STORE_OWNER)),
):
    """Onboard a new store."""
    store = Store(
        org_id=user.org_id,
        name=body.name,
        city=body.city,
        state=body.state,
        pincode=body.pincode,
        address=body.address,
        num_aisles=body.num_aisles,
        shelves_per_aisle=body.shelves_per_aisle,
        sections_per_shelf=body.sections_per_shelf,
    )
    db.add(store)
    await db.flush()

    await log_action(db, "store.create", user_id=user.sub, resource_type="store", resource_id=store.id)

    return StoreResponse(
        id=store.id,
        name=store.name,
        city=store.city,
        state=store.state,
        pincode=store.pincode,
        num_aisles=store.num_aisles,
        shelves_per_aisle=store.shelves_per_aisle,
        sections_per_shelf=store.sections_per_shelf,
        timezone=store.timezone,
        created_at=store.created_at,
    )


@router.get("", response_model=list[StoreResponse])
async def list_stores(
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """List all stores for the user's organization."""
    query = select(Store)
    if user.org_id:
        query = query.where(Store.org_id == user.org_id)
    result = await db.execute(query)
    stores = result.scalars().all()

    return [
        StoreResponse(
            id=s.id, name=s.name, city=s.city, state=s.state,
            pincode=s.pincode, num_aisles=s.num_aisles,
            shelves_per_aisle=s.shelves_per_aisle,
            sections_per_shelf=s.sections_per_shelf,
            timezone=s.timezone, created_at=s.created_at,
        )
        for s in stores
    ]


# ── Cameras ──────────────────────────────────────────────────

@router.get("/{store_id}/cameras", response_model=list[CameraResponse])
async def list_cameras(
    store_id: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(get_current_user),
):
    """List cameras registered to a store."""
    result = await db.execute(select(Camera).where(Camera.store_id == store_id))
    cameras = result.scalars().all()

    return [
        CameraResponse(
            id=c.id, name=c.name, aisle=c.aisle,
            status=c.status, last_frame_at=c.last_frame_at,
        )
        for c in cameras
    ]


@router.post("/{store_id}/cameras", response_model=CameraResponse, status_code=status.HTTP_201_CREATED)
async def register_camera(
    store_id: str,
    body: CameraCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role(UserRole.STORE_OWNER)),
):
    """Register a new camera (RTSP URL is encrypted before storage)."""
    camera = Camera(
        store_id=store_id,
        name=body.name,
        rtsp_url_enc=encrypt_field(body.rtsp_url),
        aisle=body.aisle,
    )
    db.add(camera)
    await db.flush()

    await log_action(db, "camera.register", user_id=user.sub, resource_type="camera", resource_id=camera.id)

    return CameraResponse(
        id=camera.id, name=camera.name, aisle=camera.aisle,
        status=camera.status, last_frame_at=camera.last_frame_at,
    )


# ── Associates ───────────────────────────────────────────────

@router.get("/{store_id}/associates", response_model=list[AssociateResponse])
async def list_associates(
    store_id: str,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role(UserRole.STORE_MANAGER)),
):
    """List associates for a store (phone numbers masked)."""
    result = await db.execute(select(Associate).where(Associate.store_id == store_id))
    associates = result.scalars().all()

    return [
        AssociateResponse(
            id=a.id, name=a.name,
            whatsapp_masked=mask_phone(decrypt_field(a.whatsapp_enc)) if a.whatsapp_enc else "N/A",
            language=a.language, role=a.role, is_active=a.is_active,
        )
        for a in associates
    ]


@router.post("/{store_id}/associates", response_model=AssociateResponse, status_code=status.HTTP_201_CREATED)
async def add_associate(
    store_id: str,
    body: AssociateCreate,
    db: AsyncSession = Depends(get_db),
    user: TokenPayload = Depends(require_role(UserRole.STORE_MANAGER)),
):
    """Add a store associate with encrypted WhatsApp number."""
    associate = Associate(
        store_id=store_id,
        name=body.name,
        whatsapp_enc=encrypt_field(body.whatsapp_number),
        language=body.language,
        role=body.role,
    )
    db.add(associate)
    await db.flush()

    await log_action(db, "associate.add", user_id=user.sub, resource_type="associate", resource_id=associate.id)

    return AssociateResponse(
        id=associate.id, name=associate.name,
        whatsapp_masked=mask_phone(body.whatsapp_number),
        language=associate.language, role=associate.role, is_active=True,
    )
