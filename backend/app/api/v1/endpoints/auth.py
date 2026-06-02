"""
Auth endpoints — Login, refresh, logout.
"""
from fastapi import APIRouter, HTTPException, Response, status

from backend.app.core.security import (
    DEMO_USERS,
    create_access_token,
    create_refresh_token,
    verify_password,
)
from backend.app.schemas.schemas import LoginRequest, TokenResponse, UserInfo

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response):
    """
    Authenticate user and return JWT tokens.

    Access token: returned in response body (store in memory only, never localStorage).
    Refresh token: set as httpOnly cookie.
    """
    user = DEMO_USERS.get(body.email)
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        user_id=user["user_id"],
        role=user["role"],
        org_id=user.get("org_id"),
    )
    refresh_token = create_refresh_token(
        user_id=user["user_id"],
        role=user["role"],
        org_id=user.get("org_id"),
    )

    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set True in production (HTTPS only)
        samesite="strict",
        max_age=7 * 24 * 3600,  # 7 days
    )

    from backend.app.core.config import settings
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        user=UserInfo(
            user_id=user["user_id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            org_id=user.get("org_id"),
        ),
    )


@router.post("/refresh")
async def refresh_token(response: Response):
    """
    Refresh the access token using the httpOnly refresh cookie.
    """
    # In a real implementation, read from request.cookies["refresh_token"]
    # For now, return a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Refresh token endpoint — requires cookie-based refresh flow.",
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout by clearing the refresh token cookie.
    In production, also add the token JTI to the Redis blocklist.
    """
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}
