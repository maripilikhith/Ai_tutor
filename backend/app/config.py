"""
AI Study Companion — Application Configuration

Loads all settings from environment variables using Pydantic Settings.
Every config value is centralized here — no scattered os.getenv() calls.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # ── Supabase ──
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    # ── Google AI (Gemini) ──
    gemini_api_key: str = ""

    # ── Redis (Upstash) ──
    upstash_redis_url: str = ""
    upstash_redis_token: str = ""

    # ── App Config ──
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    environment: str = "development"

    # ── AI Model Config ──
    gemini_model: str = "gemini-3.5-flash"
    embedding_model: str = "gemini-embedding-001"
    embedding_dimension: int = 768  # Must match the vector column in knowledge_chunks

    # ── Processing Config ──
    chunk_size: int = 600          # Target tokens per chunk
    chunk_overlap: int = 100       # Overlap between chunks
    max_upload_size_mb: int = 50   # Max PDF upload size
    retrieval_top_k: int = 5       # Number of chunks to retrieve
    similarity_threshold: float = 0.4  # Min similarity for retrieval

    # ── Rate Limiting ──
    rate_limit_requests: int = 30  # Requests per window
    rate_limit_window: int = 60    # Window in seconds

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Returns cached Settings instance.
    Using lru_cache so .env is read only once.
    """
    return Settings()
