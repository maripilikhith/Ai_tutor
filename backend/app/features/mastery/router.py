"""
Mastery Feature — API Routes
"""

from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.features.mastery import service, schemas

router = APIRouter()


@router.get("/projects/{project_id}/mastery", response_model=schemas.MasteryListResponse)
async def get_mastery(project_id: str, current_user: CurrentUser):
    """Get all concept mastery scores for a project."""
    return await service.get_mastery(project_id, current_user["user_id"])


@router.get("/projects/{project_id}/growth", response_model=schemas.GrowthResponse)
async def get_growth(project_id: str, current_user: CurrentUser):
    """Get mastery growth data for charts."""
    return await service.get_growth_data(project_id, current_user["user_id"])
