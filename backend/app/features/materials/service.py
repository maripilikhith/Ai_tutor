"""
Materials Feature — Business Logic

Handles file upload, status tracking, and processing orchestration.
The actual processing pipeline is in processor.py.
"""

from app.core.database.supabase import get_supabase
from app.core.storage.supabase_storage import upload_file
from app.core.events.logger import log_event
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.core.auth.permissions import check_ownership
from app.config import get_settings


async def list_materials(project_id: str, user_id: str) -> dict:
    """List all materials for a project."""
    db = get_supabase()

    result = db.table("materials") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    return {"items": result.data or [], "total": len(result.data or [])}


async def get_material(material_id: str, user_id: str) -> dict:
    """Get a single material with status."""
    db = get_supabase()

    result = db.table("materials") \
        .select("*") \
        .eq("id", material_id) \
        .single() \
        .execute()

    if not result.data:
        raise NotFoundError("Material", material_id)

    if not check_ownership(result.data["user_id"], user_id):
        raise ForbiddenError()

    return result.data


async def upload_material(
    project_id: str,
    user_id: str,
    file_name: str,
    file_content: bytes,
    file_type: str = "application/pdf",
) -> dict:
    """
    Upload a PDF file and queue it for processing.

    Steps:
    1. Validate file type and size
    2. Upload to Supabase Storage
    3. Create material record (status: queued)
    4. Create background job for processing
    5. Log the event

    Returns:
        The created material record
    """
    settings = get_settings()

    # Validate file type
    if file_type != "application/pdf":
        raise BadRequestError("Only PDF files are supported")

    # Validate file size
    max_size = settings.max_upload_size_mb * 1024 * 1024
    if len(file_content) > max_size:
        raise BadRequestError(f"File too large. Max size: {settings.max_upload_size_mb}MB")

    # Verify project exists and belongs to user
    db = get_supabase()
    project = db.table("projects") \
        .select("id") \
        .eq("id", project_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not project.data:
        raise NotFoundError("Project", project_id)

    # Upload file to storage
    storage_path = f"{user_id}/{project_id}/{file_name}"
    await upload_file(file_content, storage_path, file_type)

    # Create material record
    result = db.table("materials") \
        .insert({
            "user_id": user_id,
            "project_id": project_id,
            "file_name": file_name,
            "file_size_bytes": len(file_content),
            "file_type": file_type,
            "storage_path": storage_path,
            "status": "queued",
        }) \
        .execute()

    material = result.data[0]

    # Create background job for document processing
    db.table("background_jobs") \
        .insert({
            "user_id": user_id,
            "job_type": "process_material",
            "payload": {
                "material_id": material["id"],
                "project_id": project_id,
                "storage_path": storage_path,
                "file_name": file_name,
            },
            "priority": 3,  # High priority for document processing
        }) \
        .execute()

    await log_event(
        user_id=user_id,
        event_type="material_uploaded",
        event_data={"file_name": file_name, "file_size": len(file_content)},
        project_id=project_id,
    )

    return material


async def get_processing_status(material_id: str, user_id: str) -> dict:
    """Get detailed processing status for a material."""
    material = await get_material(material_id, user_id)
    db = get_supabase()

    # Count chunks created
    chunks = db.table("knowledge_chunks") \
        .select("id", count="exact") \
        .eq("material_id", material_id) \
        .execute()

    # Count concepts extracted
    concepts = db.table("concepts") \
        .select("id", count="exact") \
        .eq("project_id", material["project_id"]) \
        .eq("user_id", user_id) \
        .execute()

    return {
        "material_id": material_id,
        "status": material["status"],
        "page_count": material.get("page_count", 0),
        "chunks_created": chunks.count or 0,
        "concepts_extracted": concepts.count or 0,
        "error_message": material.get("error_message"),
    }


async def delete_material(material_id: str, user_id: str) -> None:
    """Delete a material and its associated chunks."""
    material = await get_material(material_id, user_id)

    db = get_supabase()

    # Delete chunks first (cascade might handle this, but be explicit)
    db.table("knowledge_chunks") \
        .delete() \
        .eq("material_id", material_id) \
        .execute()

    # Delete the material record
    db.table("materials") \
        .delete() \
        .eq("id", material_id) \
        .execute()

    # Delete from storage
    from app.core.storage.supabase_storage import delete_file
    try:
        await delete_file(material["storage_path"])
    except Exception:
        pass  # Storage cleanup is best-effort
