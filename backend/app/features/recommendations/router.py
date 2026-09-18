"""Recommendations Feature — API Routes"""
from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.features.recommendations import service, schemas

router = APIRouter()

@router.get("/projects/{project_id}/recommendations", response_model=schemas.RecommendationListResponse)
async def get_recommendations(project_id: str, current_user: CurrentUser):
    return await service.get_recommendations(project_id, current_user["user_id"])

@router.post("/projects/{project_id}/recommendations/generate")
async def generate_recommendations(project_id: str, current_user: CurrentUser):
    return await service.generate_recommendations(project_id, current_user["user_id"])

@router.put("/recommendations/{rec_id}/complete")
async def complete_recommendation(rec_id: str, current_user: CurrentUser):
    return await service.update_recommendation(rec_id, current_user["user_id"], "completed")

@router.put("/recommendations/{rec_id}/dismiss")
async def dismiss_recommendation(rec_id: str, current_user: CurrentUser):
    return await service.update_recommendation(rec_id, current_user["user_id"], "dismissed")
