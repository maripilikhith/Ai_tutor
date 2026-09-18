"""
Projects Feature — Pydantic Schemas

Request/response models for the Projects API.
"""

from pydantic import BaseModel, Field
from datetime import datetime


# ── Request Schemas ──

class ProjectCreate(BaseModel):
    """Create a new project within a space."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=1000)
    learning_goal: str = Field("", max_length=500)
    space_id: str


class ProjectUpdate(BaseModel):
    """Update an existing project."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    learning_goal: str | None = Field(None, max_length=500)
    status: str | None = Field(None, pattern=r"^(active|archived|completed)$")


# ── Response Schemas ──

class ProjectResponse(BaseModel):
    """Project response with computed stats."""
    id: str
    space_id: str
    name: str
    description: str
    learning_goal: str
    status: str
    material_count: int = 0
    quiz_count: int = 0
    avg_mastery: float = 0.0
    created_at: datetime
    updated_at: datetime


class ProjectDashboard(BaseModel):
    """Full project dashboard data."""
    project: ProjectResponse
    recent_activity: list[dict] = []
    mastery_summary: list[dict] = []
    recommendations: list[dict] = []
    stats: dict = {}


class ProjectListResponse(BaseModel):
    """Paginated list of projects."""
    items: list[ProjectResponse]
    total: int
