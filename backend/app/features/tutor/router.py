"""
Tutor Feature — API Routes

Streaming chat endpoint + conversation management.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.dependencies import CurrentUser
from app.features.tutor import service, schemas

router = APIRouter()


@router.post("/projects/{project_id}/tutor/chat")
async def chat(
    project_id: str,
    data: schemas.ChatMessageRequest,
    current_user: CurrentUser,
):
    """
    Send a message to the AI Tutor and stream the response.

    Returns a Server-Sent Events (SSE) stream with:
    - type: "conversation_id" — the conversation ID
    - type: "content" — text chunks as they arrive
    - type: "citations" — extracted source citations
    - type: "suggestions" — follow-up question suggestions
    - type: "done" — stream complete
    """
    return StreamingResponse(
        service.chat(
            project_id=project_id,
            user_id=current_user["user_id"],
            message=data.message,
            conversation_id=data.conversation_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get(
    "/projects/{project_id}/conversations",
    response_model=schemas.ConversationListResponse,
)
async def list_conversations(project_id: str, current_user: CurrentUser):
    """List all conversations for a project."""
    return await service.list_conversations(project_id, current_user["user_id"])


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, current_user: CurrentUser):
    """Get a conversation with all its messages."""
    return await service.get_conversation_messages(
        conversation_id, current_user["user_id"]
    )
