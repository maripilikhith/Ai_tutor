"""
Spaces Feature — Pydantic Schemas

Request/response models for the Spaces API.
"""

from pydantic import BaseModel, Field
from datetime import datetime

class ProjectSimple(BaseModel):
    id: str
    name: str


# ── Request Schemas ──

class SpaceCreate(BaseModel):
    """Create a new space."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    color: str = Field("#6C5CE7", pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str = Field("📚", max_length=4)


class SpaceUpdate(BaseModel):
    """Update an existing space."""
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: str | None = Field(None, max_length=4)


# ── Response Schemas ──

class SpaceResponse(BaseModel):
    """Space response with computed stats."""
    id: str
    name: str
    description: str
    color: str
    icon: str
    project_count: int = 0
    projects: list[ProjectSimple] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SpaceListResponse(BaseModel):
    """Paginated list of spaces."""
    items: list[SpaceResponse]
    total: int
