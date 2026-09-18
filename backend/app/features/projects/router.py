"""
Projects Feature — API Routes

CRUD endpoints for projects + project dashboard.
"""

from fastapi import APIRouter, Query
from app.dependencies import CurrentUser
from app.features.projects import service, schemas

router = APIRouter(prefix="/projects")


@router.get("", response_model=schemas.ProjectListResponse)
async def list_projects(
    current_user: CurrentUser,
    space_id: str | None = Query(None, description="Filter by space"),
):
    """List projects, optionally filtered by space."""
    return await service.list_projects(current_user["user_id"], space_id)


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
async def get_project(project_id: str, current_user: CurrentUser):
    """Get a single project with stats."""
    return await service.get_project(project_id, current_user["user_id"])


@router.get("/{project_id}/dashboard", response_model=schemas.ProjectDashboard)
async def get_project_dashboard(project_id: str, current_user: CurrentUser):
    """Get the full project dashboard with activity, mastery, recommendations."""
    return await service.get_project_dashboard(project_id, current_user["user_id"])


@router.post("", response_model=schemas.ProjectResponse, status_code=201)
async def create_project(data: schemas.ProjectCreate, current_user: CurrentUser):
    """Create a new project within a space."""
    return await service.create_project(current_user["user_id"], data.model_dump())


@router.put("/{project_id}", response_model=schemas.ProjectResponse)
async def update_project(
    project_id: str,
    data: schemas.ProjectUpdate,
    current_user: CurrentUser,
):
    """Update a project's details."""
    return await service.update_project(
        project_id, current_user["user_id"], data.model_dump(exclude_none=True)
    )


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, current_user: CurrentUser):
    """Delete a project and all related data."""
    await service.delete_project(project_id, current_user["user_id"])
