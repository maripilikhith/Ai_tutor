"""
AI Study Companion — Custom Exception Classes

All custom exceptions used across the application.
Each exception maps to an appropriate HTTP status code.
"""

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Resource not found (404)."""
    def __init__(self, resource: str, resource_id: str = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} '{resource_id}' not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ForbiddenError(HTTPException):
    """User doesn't have permission to access this resource (403)."""
    def __init__(self, detail: str = "You don't have permission to access this resource"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestError(HTTPException):
    """Invalid request data (400)."""
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class ConflictError(HTTPException):
    """Resource already exists or conflicts (409)."""
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class AIServiceError(HTTPException):
    """AI service (Gemini) encountered an error (502)."""
    def __init__(self, detail: str = "AI service temporarily unavailable"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail)


class RateLimitError(HTTPException):
    """Too many requests (429)."""
    def __init__(self, detail: str = "Too many requests. Please try again later."):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=detail)


class ProcessingError(HTTPException):
    """Background processing failed (500)."""
    def __init__(self, detail: str = "Processing failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
