"""
Materials Feature — API Routes

Upload, list, status check, and delete endpoints for learning materials.
"""

from fastapi import APIRouter, UploadFile, File
from app.dependencies import CurrentUser
from app.features.materials import service, schemas

router = APIRouter(prefix="/projects/{project_id}/materials")


@router.get("", response_model=schemas.MaterialListResponse)
async def list_materials(project_id: str, current_user: CurrentUser):
    """List all materials for a project."""
    return await service.list_materials(project_id, current_user["user_id"])


@router.post("", response_model=schemas.MaterialResponse, status_code=201)
async def upload_material(
    project_id: str,
    current_user: CurrentUser,
    file: UploadFile = File(..., description="PDF file to upload"),
):
    """Upload a PDF file for processing."""
    content = await file.read()
    return await service.upload_material(
        project_id=project_id,
        user_id=current_user["user_id"],
        file_name=file.filename or "document.pdf",
        file_content=content,
        file_type=file.content_type or "application/pdf",
    )


@router.get("/{material_id}", response_model=schemas.MaterialResponse)
async def get_material(material_id: str, current_user: CurrentUser):
    """Get a single material's details."""
    return await service.get_material(material_id, current_user["user_id"])


@router.get("/{material_id}/status", response_model=schemas.ProcessingStatus)
async def get_processing_status(material_id: str, current_user: CurrentUser):
    """Get detailed processing status for a material."""
    return await service.get_processing_status(material_id, current_user["user_id"])


@router.delete("/{material_id}", status_code=204)
async def delete_material(material_id: str, current_user: CurrentUser):
    """Delete a material and its knowledge chunks."""
    await service.delete_material(material_id, current_user["user_id"])
