"""Admin Feature — API Routes (admin-only)"""
from fastapi import APIRouter, Query
from app.dependencies import AdminUser
from app.features.admin import service

router = APIRouter(prefix="/admin")

@router.get("/dashboard")
async def get_admin_dashboard(current_user: AdminUser):
    return await service.get_admin_dashboard()

@router.get("/users")
async def list_users(current_user: AdminUser, page: int = Query(1), page_size: int = Query(20)):
    return await service.list_users(page, page_size)

@router.get("/users/{user_id}")
async def get_user_detail(user_id: str, current_user: AdminUser):
    return await service.get_user_detail(user_id)

@router.get("/ai-usage")
async def get_ai_usage(current_user: AdminUser):
    return await service.get_ai_usage_stats()

@router.get("/activity-log")
async def get_activity_log(current_user: AdminUser, page: int = Query(1)):
    return await service.get_activity_log(page)

@router.get("/health")
async def get_system_health(current_user: AdminUser):
    return await service.get_system_health()
