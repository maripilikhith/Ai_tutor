"""
Spaces Feature — API Routes

CRUD endpoints for managing learning spaces.
"""

from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.features.spaces import service, schemas

router = APIRouter(prefix="/spaces")


@router.get("", response_model=schemas.SpaceListResponse)
async def list_spaces(current_user: CurrentUser):
    """List all spaces for the authenticated user."""
    result = await service.list_spaces(current_user["user_id"])
    return result


@router.get("/{space_id}", response_model=schemas.SpaceResponse)
async def get_space(space_id: str, current_user: CurrentUser):
    """Get a single space by ID."""
    return await service.get_space(space_id, current_user["user_id"])


@router.post("", response_model=schemas.SpaceResponse, status_code=201)
async def create_space(data: schemas.SpaceCreate, current_user: CurrentUser):
    """Create a new learning space."""
    return await service.create_space(current_user["user_id"], data.model_dump())


@router.put("/{space_id}", response_model=schemas.SpaceResponse)
async def update_space(
    space_id: str,
    data: schemas.SpaceUpdate,
    current_user: CurrentUser,
):
    """Update a space's details."""
    return await service.update_space(
        space_id, current_user["user_id"], data.model_dump(exclude_none=True)
    )


@router.delete("/{space_id}", status_code=204)
async def delete_space(space_id: str, current_user: CurrentUser):
    """Delete a space and all its projects."""
    await service.delete_space(space_id, current_user["user_id"])
