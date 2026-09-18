"""
Tutor Feature — Pydantic Schemas

Request/response models for the AI Tutor chat.
"""

from pydantic import BaseModel, Field
from datetime import datetime


class ChatMessageRequest(BaseModel):
    """Send a message to the AI Tutor."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: str | None = None  # None creates a new conversation


class Citation(BaseModel):
    """A source citation from the AI response."""
    file_name: str
    page_number: int | None = None
    chunk_id: str | None = None


class ChatMessageResponse(BaseModel):
    """Response from the AI Tutor (for non-streaming)."""
    conversation_id: str
    message_id: str
    content: str
    citations: list[Citation] = []
    suggested_questions: list[str] = []


class ConversationResponse(BaseModel):
    """Conversation summary."""
    id: str
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """List of conversations."""
    items: list[ConversationResponse]
    total: int


class MessageResponse(BaseModel):
    """A single message in a conversation."""
    id: str
    role: str
    content: str
    citations: list[dict] = []
    created_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with all messages."""
    conversation: ConversationResponse
    messages: list[MessageResponse]
