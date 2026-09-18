"""Profile Feature — API Routes"""

from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.features.profile import service, schemas

router = APIRouter(prefix="/profile")


@router.get("", response_model=schemas.ProfileResponse)
async def get_profile(current_user: CurrentUser):
    """Get the current user's profile."""
    return await service.get_profile(current_user["user_id"])


@router.put("", response_model=schemas.ProfileResponse)
async def update_profile(data: schemas.ProfileUpdate, current_user: CurrentUser):
    """Update the current user's profile (name, bio, avatar_url)."""
    return await service.update_profile(current_user["user_id"], data.model_dump(exclude_none=True))
