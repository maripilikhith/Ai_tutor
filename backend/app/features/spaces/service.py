"""
Spaces Feature — Business Logic

All space-related operations: CRUD + project count aggregation.
Pure business logic — no HTTP or FastAPI concepts here.
"""

from app.core.database.supabase import get_supabase
from app.core.events.logger import log_event
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.auth.permissions import check_ownership


async def list_spaces(user_id: str) -> dict:
    """
    List all spaces for a user with project counts.

    Returns:
        { items: [...], total: int }
    """
    db = get_supabase()

    # Get spaces
    result = db.table("spaces") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    spaces = result.data or []

    # Get project counts per space
    for space in spaces:
        projects_result = db.table("projects") \
            .select("id, name") \
            .eq("space_id", space["id"]) \
            .eq("user_id", user_id) \
            .order("name") \
            .execute()
        
        space["projects"] = projects_result.data or []
        space["project_count"] = len(space["projects"])

    return {
        "items": spaces,
        "total": len(spaces),
    }


async def get_space(space_id: str, user_id: str) -> dict:
    """
    Get a single space by ID.

    Raises:
        NotFoundError if space doesn't exist
        ForbiddenError if user doesn't own the space
    """
    db = get_supabase()

    result = db.table("spaces") \
        .select("*") \
        .eq("id", space_id) \
        .single() \
        .execute()

    space = result.data
    if not space:
        raise NotFoundError("Space", space_id)

    if not check_ownership(space["user_id"], user_id):
        raise ForbiddenError()

    # Add project count
    count_result = db.table("projects") \
        .select("id", count="exact") \
        .eq("space_id", space_id) \
        .execute()
    space["project_count"] = count_result.count or 0

    return space


async def create_space(user_id: str, data: dict) -> dict:
    """
    Create a new space.

    Args:
        user_id: The owner's user ID
        data: Space creation data (name, description, color, icon)

    Returns:
        The created space
    """
    db = get_supabase()

    result = db.table("spaces") \
        .insert({
            "user_id": user_id,
            "name": data["name"],
            "description": data.get("description", ""),
            "color": data.get("color", "#6C5CE7"),
            "icon": data.get("icon", "📚"),
        }) \
        .execute()

    space = result.data[0]
    space["project_count"] = 0

    # Log the event
    await log_event(
        user_id=user_id,
        event_type="space_created",
        event_data={"space_name": data["name"]},
        space_id=space["id"],
    )

    return space


async def update_space(space_id: str, user_id: str, data: dict) -> dict:
    """
    Update a space's name, description, color, or icon.

    Only updates fields that are provided (not None).
    """
    # Verify ownership
    await get_space(space_id, user_id)

    db = get_supabase()

    # Filter out None values
    update_data = {k: v for k, v in data.items() if v is not None}

    if not update_data:
        return await get_space(space_id, user_id)

    result = db.table("spaces") \
        .update(update_data) \
        .eq("id", space_id) \
        .eq("user_id", user_id) \
        .execute()

    return await get_space(space_id, user_id)


async def delete_space(space_id: str, user_id: str) -> None:
    """
    Delete a space and all its projects (cascading).

    Raises:
        NotFoundError if space doesn't exist
        ForbiddenError if user doesn't own the space
    """
    # Verify ownership
    await get_space(space_id, user_id)

    db = get_supabase()
    db.table("spaces") \
        .delete() \
        .eq("id", space_id) \
        .eq("user_id", user_id) \
        .execute()
