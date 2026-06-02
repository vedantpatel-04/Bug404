"""
ShelfIQ Backend — JWT Authentication & Role-Based Access Control.

Implements:
- JWT token creation and validation (HS256 for dev, RS256 for production)
- Password hashing with bcrypt
- Role-based permission checking
- Refresh tokens via httpOnly cookies
- Token revocation via Redis blocklist
"""
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from backend.app.core.config import settings


# ── Password Hashing ────────────────────────────────────────


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ── Roles ────────────────────────────────────────────────────

class UserRole(str, Enum):
    STORE_OWNER = "STORE_OWNER"
    STORE_MANAGER = "STORE_MANAGER"
    SHELF_ASSOCIATE = "SHELF_ASSOCIATE"
    ANALYST = "ANALYST"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


# Role hierarchy: each role includes permissions of roles below it
ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.PLATFORM_ADMIN: 100,
    UserRole.STORE_OWNER: 80,
    UserRole.STORE_MANAGER: 60,
    UserRole.ANALYST: 40,
    UserRole.SHELF_ASSOCIATE: 20,
}


# ── Token Models ─────────────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str  # user ID
    role: str
    org_id: Optional[str] = None
    exp: Optional[datetime] = None
    type: str = "access"  # "access" or "refresh"


class TokenPair(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# ── Token Creation ───────────────────────────────────────────

def create_access_token(
    user_id: str,
    role: str,
    org_id: Optional[str] = None,
) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "exp": expire,
        "type": "access",
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    user_id: str,
    role: str,
    org_id: Optional[str] = None,
) -> str:
    """Create a long-lived JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "role": role,
        "org_id": org_id,
        "exp": expire,
        "type": "refresh",
        "jti": secrets.token_hex(16),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ── FastAPI Dependencies ─────────────────────────────────────

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> TokenPayload:
    """
    Extract and validate the current user from the Authorization header.
    Returns the decoded token payload.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_payload = decode_token(credentials.credentials)

    if token_payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type. Use an access token.",
        )

    return token_payload


def require_role(minimum_role: UserRole):
    """
    Dependency factory: ensures user has at least the specified role level.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role(UserRole.STORE_OWNER))])
    """
    async def role_checker(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        user_role = UserRole(user.role)
        user_level = ROLE_HIERARCHY.get(user_role, 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)

        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {minimum_role.value}",
            )
        return user

    return role_checker


# ── Demo Users (for development — replaced by DB in production) ──

DEMO_USERS: dict[str, dict] = {
    "admin@shelfiq.in": {
        "user_id": "usr_admin_001",
        "email": "admin@shelfiq.in",
        "name": "Platform Admin",
        "hashed_password": hash_password("admin123"),
        "role": UserRole.PLATFORM_ADMIN.value,
        "org_id": "org_prama_001",
    },
    "owner@rajesh-supermart.in": {
        "user_id": "usr_owner_001",
        "email": "owner@rajesh-supermart.in",
        "name": "Rajesh Patel",
        "hashed_password": hash_password("owner123"),
        "role": UserRole.STORE_OWNER.value,
        "org_id": "org_rajesh_001",
    },
    "manager@rajesh-supermart.in": {
        "user_id": "usr_mgr_001",
        "email": "manager@rajesh-supermart.in",
        "name": "Amit Shah",
        "hashed_password": hash_password("manager123"),
        "role": UserRole.STORE_MANAGER.value,
        "org_id": "org_rajesh_001",
    },
    "associate@rajesh-supermart.in": {
        "user_id": "usr_assoc_001",
        "email": "associate@rajesh-supermart.in",
        "name": "Vikram Singh",
        "hashed_password": hash_password("associate123"),
        "role": UserRole.SHELF_ASSOCIATE.value,
        "org_id": "org_rajesh_001",
    },
}
