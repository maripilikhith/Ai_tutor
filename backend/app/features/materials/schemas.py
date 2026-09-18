"""
Materials Feature — Pydantic Schemas

Request/response models for material upload and management.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class MaterialResponse(BaseModel):
    """Material response with processing status."""
    id: str
    project_id: str
    file_name: str
    file_size_bytes: int
    file_type: str
    status: str
    page_count: int
    error_message: str | None = None
    processed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class MaterialListResponse(BaseModel):
    """List of materials for a project."""
    items: list[MaterialResponse]
    total: int


class ProcessingStatus(BaseModel):
    """Detailed processing status for a material."""
    material_id: str
    status: str
    page_count: int
    chunks_created: int = 0
    concepts_extracted: int = 0
    error_message: str | None = None
