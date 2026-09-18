"""Admin Feature — Schemas"""
from pydantic import BaseModel
from datetime import datetime

class AdminUserResponse(BaseModel):
    id: str
    full_name: str
    email: str = ""
    role: str
    space_count: int = 0
    project_count: int = 0
    quiz_count: int = 0
    created_at: datetime

class SystemHealthResponse(BaseModel):
    status: str
    database: str = "connected"
    ai_service: str = "connected"
    cache: str = "connected"
    pending_jobs: int = 0
    failed_jobs: int = 0
