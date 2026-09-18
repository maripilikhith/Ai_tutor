"""Profile Feature — Business Logic"""

from app.core.database.supabase import get_supabase
from app.core.exceptions import NotFoundError


async def get_profile(user_id: str) -> dict:
    """Get the current user's profile from the profiles table."""
    db = get_supabase()

    result = db.table("profiles") \
        .select("*") \
        .eq("id", user_id) \
        .single() \
        .execute()

    if not result.data:
        raise NotFoundError("Profile", user_id)

    profile = result.data

    # Fetch email from auth.users via admin client (profiles table doesn't store email)
    try:
        from app.config import get_settings
        from supabase import create_client
        settings = get_settings()
        admin_db = create_client(settings.supabase_url, settings.supabase_service_key)
        auth_user = admin_db.auth.admin.get_user_by_id(user_id)
        if auth_user and auth_user.user:
            profile["email"] = auth_user.user.email or ""
    except Exception:
        profile["email"] = ""

    return profile


async def update_profile(user_id: str, data: dict) -> dict:
    """Update the user's profile fields."""
    db = get_supabase()

    # Only update fields that exist in the profiles table
    # bio is optional — skip it if the column doesn't exist yet
    allowed_columns = {"full_name", "avatar_url", "bio", "timezone", "use_custom_key", "gemini_api_key"}
    update_data = {k: v for k, v in data.items() if k in allowed_columns and v is not None}

    if not update_data:
        return await get_profile(user_id)

    try:
        db.table("profiles") \
            .update(update_data) \
            .eq("id", user_id) \
            .execute()
    except Exception:
        # If bio column doesn't exist yet, retry without it
        update_data.pop("bio", None)
        if update_data:
            db.table("profiles") \
                .update(update_data) \
                .eq("id", user_id) \
                .execute()

    return await get_profile(user_id)

