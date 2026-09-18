"""
AI Study Companion — JWT Token Verification

Verifies Supabase-issued JWT tokens on every authenticated request.
Extracts user_id and role from the token claims.

Verification order:
  1. Local HS256 decode (fast, if SUPABASE_JWT_SECRET is configured)
  2. Supabase Auth API call (always works, slightly slower)
  3. Unverified decode fallback in development (never in production)
"""

import logging
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.config import get_settings

logger = logging.getLogger(__name__)


async def verify_token(token: str) -> dict:
    """
    Verify a Supabase JWT token and extract user claims.

    Args:
        token: The JWT token string (without 'Bearer ' prefix)

    Returns:
        dict with:
            - user_id: str (UUID from the 'sub' claim)
            - role: str ('user' or 'admin')
            - email: str (user's email)

    Raises:
        HTTPException 401 if token is invalid or expired
    """
    settings = get_settings()

    # ── Strategy 1: Local HS256 decode (fast path) ──
    jwt_secret = settings.supabase_jwt_secret
    if jwt_secret and jwt_secret not in ("", "PASTE_YOUR_JWT_SECRET_HERE"):
        try:
            payload = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
            user_id = payload.get("sub")
            if user_id:
                role = _extract_role(payload)
                logger.debug("Token verified via local JWT decode for user %s", user_id)
                return {
                    "user_id": user_id,
                    "role": role,
                    "email": payload.get("email", ""),
                }
        except JWTError as e:
            logger.warning("Local JWT decode failed: %s — trying Supabase API", e)

    # ── Strategy 2: Supabase Auth API verification ──
    try:
        from app.core.database.supabase import get_supabase_anon
        res = get_supabase_anon().auth.get_user(token)
        if res and res.user:
            u = res.user
            app_meta = getattr(u, "app_metadata", {}) or {}
            user_meta = getattr(u, "user_metadata", {}) or {}
            role = app_meta.get("role") or user_meta.get("role") or "user"
            logger.debug("Token verified via Supabase API for user %s", u.id)
            return {
                "user_id": str(u.id),
                "role": role,
                "email": u.email or "",
            }
        else:
            logger.warning("Supabase auth.get_user returned no user")
    except Exception as e:
        logger.warning("Supabase API verification failed: %s", e)

    # ── Strategy 3: Dev-only unverified decode ──
    # This lets development proceed without the JWT secret configured.
    # The token was still issued by Supabase — we just skip signature check.
    if settings.environment == "development":
        try:
            payload = jwt.get_unverified_claims(token)
            user_id = payload.get("sub")
            # Only trust unverified tokens that have a valid Supabase issuer
            iss = payload.get("iss", "")
            if user_id and "supabase" in iss:
                role = _extract_role(payload)
                logger.warning(
                    "⚠ Token accepted via UNVERIFIED decode (dev mode). "
                    "Set SUPABASE_JWT_SECRET in backend/.env for production."
                )
                return {
                    "user_id": user_id,
                    "role": role,
                    "email": payload.get("email", ""),
                }
        except Exception as e:
            logger.warning("Unverified decode failed: %s", e)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token — please log in again",
        headers={"WWW-Authenticate": "Bearer"},
    )


def _extract_role(payload: dict) -> str:
    """Extract user role from JWT payload claims."""
    app_metadata = payload.get("app_metadata", {}) or {}
    user_metadata = payload.get("user_metadata", {}) or {}
    role = app_metadata.get("role", "user")
    if role == "user" and user_metadata.get("role"):
        role = user_metadata["role"]
    return role
