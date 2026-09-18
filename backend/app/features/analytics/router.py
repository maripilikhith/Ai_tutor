"""Analytics Feature — API Routes"""
from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.features.analytics import service

router = APIRouter()

@router.get("/projects/{project_id}/analytics")
async def get_project_analytics(project_id: str, current_user: CurrentUser):
    return await service.get_project_analytics(project_id, current_user["user_id"])

@router.get("/analytics")
async def get_global_analytics(current_user: CurrentUser):
    return await service.get_global_analytics(current_user["user_id"])
