"""
AI Study Companion — Supabase Storage Client

Handles file upload, download, and deletion in Supabase Storage.
Used for PDF document management.
"""

from app.core.database.supabase import get_supabase

BUCKET_NAME = "materials"


async def upload_file(
    file_content: bytes,
    file_path: str,
    content_type: str = "application/pdf",
) -> str:
    """
    Upload a file to Supabase Storage.

    Args:
        file_content: Raw file bytes
        file_path: Storage path (e.g., "user_id/project_id/file.pdf")
        content_type: MIME type of the file

    Returns:
        The full storage path of the uploaded file
    """
    db = get_supabase()
    db.storage.from_(BUCKET_NAME).upload(
        path=file_path,
        file=file_content,
        file_options={"content-type": content_type},
    )
    return file_path


async def download_file(file_path: str) -> bytes:
    """
    Download a file from Supabase Storage.

    Args:
        file_path: Storage path of the file

    Returns:
        Raw file bytes
    """
    db = get_supabase()
    response = db.storage.from_(BUCKET_NAME).download(file_path)
    return response


async def delete_file(file_path: str) -> None:
    """
    Delete a file from Supabase Storage.

    Args:
        file_path: Storage path of the file to delete
    """
    db = get_supabase()
    db.storage.from_(BUCKET_NAME).remove([file_path])


async def get_public_url(file_path: str) -> str:
    """
    Get the public URL for a stored file.

    Args:
        file_path: Storage path of the file

    Returns:
        Public URL string
    """
    db = get_supabase()
    response = db.storage.from_(BUCKET_NAME).get_public_url(file_path)
    return response
