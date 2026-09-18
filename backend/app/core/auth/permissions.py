"""
AI Study Companion — Auth Permissions

Helper functions for role-based access control.
Used in service layers to verify resource ownership.
"""


def check_ownership(resource_user_id: str, current_user_id: str) -> bool:
    """
    Verify that the current user owns the resource.

    Args:
        resource_user_id: The user_id stored on the resource
        current_user_id: The authenticated user's ID

    Returns:
        True if the user owns the resource

    Note:
        This is a backup check. RLS in Supabase provides the primary
        access control. This catches bugs in application code.
    """
    return str(resource_user_id) == str(current_user_id)


def is_admin(current_user: dict) -> bool:
    """Check if the current user has admin role."""
    return current_user.get("role") == "admin"
