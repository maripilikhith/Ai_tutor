"""
AI Study Companion — Shared Query Helpers

Reusable query patterns for pagination, filtering, and common operations.
Used by feature service layers to avoid repetitive query code.
"""

from typing import Any


def paginate_query(query, page: int = 1, page_size: int = 20):
    """
    Apply pagination to a Supabase query.

    Args:
        query: The Supabase query builder
        page: Page number (1-indexed)
        page_size: Number of items per page

    Returns:
        The query with range applied
    """
    start = (page - 1) * page_size
    end = start + page_size - 1
    return query.range(start, end)


def build_response_list(data: list[dict], total: int, page: int, page_size: int) -> dict:
    """
    Build a standardized paginated response.

    Returns:
        {
            "items": [...],
            "total": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5
        }
    """
    total_pages = max(1, (total + page_size - 1) // page_size)
    return {
        "items": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def safe_get(data: dict | None, key: str, default: Any = None) -> Any:
    """Safely get a value from a dict that might be None."""
    if data is None:
        return default
    return data.get(key, default)
