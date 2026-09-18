"""
AI Study Companion — Supabase Client

Initializes and provides Supabase clients for both:
- Service role (backend operations, bypasses RLS)
- Anon key (respects RLS, used with user JWT)
"""

from supabase import create_client, Client
from app.config import get_settings

# Module-level client cache
_service_client: Client | None = None
_anon_client: Client | None = None


def get_supabase_service() -> Client:
    """
    Get the Supabase client with SERVICE ROLE key.

    Use for:
    - Background job processing
    - Admin operations
    - Any operation that needs to bypass RLS

    NEVER expose this client to the frontend.
    """
    global _service_client
    if _service_client is None:
        settings = get_settings()
        _service_client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key,
        )
    return _service_client


def get_supabase_anon() -> Client:
    """
    Get the Supabase client with ANON key.

    Use for operations that should respect RLS.
    Pass the user's JWT to authenticate:
        client.auth.set_session(access_token)
    """
    global _anon_client
    if _anon_client is None:
        settings = get_settings()
        _anon_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )
    return _anon_client


def get_supabase() -> Client:
    """
    Default Supabase client for backend operations.
    Uses SERVICE ROLE key since backend is trusted.
    """
    return get_supabase_service()
