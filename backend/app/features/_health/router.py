"""
Health Check Router

Simple endpoint to verify the API is running.
Used by deployment platforms (Railway) for health monitoring.
"""

from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter()


@router.get("/api/health")
async def health_check():
    """
    Returns the current health status of the API.
    Used for deployment health checks and monitoring.
    """
    return {
        "status": "healthy",
        "service": "ai-study-companion-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
