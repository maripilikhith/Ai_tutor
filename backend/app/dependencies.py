"""
AI Study Companion — Shared FastAPI Dependencies

Dependencies injected into route handlers via FastAPI's Depends().
Centralizes auth extraction, database access, and permission checks.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status, Request

from app.config import get_settings, Settings


# ── Settings Dependency ──

def get_app_settings() -> Settings:
    """Inject application settings into route handlers."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


# ── Auth Dependencies ──
# These will be fully implemented in Phase 2 (core/auth/)

async def get_current_user(request: Request) -> dict:
    """
    Extract and verify the current user from the JWT token.

    Returns a dict with:
        - user_id: str (UUID)
        - role: str ("user" or "admin")

    Raises 401 if token is missing or invalid.
    """
    # Phase 2: Will verify Supabase JWT from Authorization header
    # For now, return a placeholder for development
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Phase 2 — verify JWT and extract user_id + role
    # For now, we'll implement the full verification in core/auth/jwt.py
    from app.core.auth.jwt import verify_token
    token = auth_header.split(" ")[1]
    return await verify_token(token)


CurrentUser = Annotated[dict, Depends(get_current_user)]


async def require_admin(current_user: CurrentUser) -> dict:
    """
    Ensure the current user has admin role.
    Use as a dependency on admin-only endpoints.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


AdminUser = Annotated[dict, Depends(require_admin)]
