"""
Tutor Feature — Business Logic

The AI Tutor service handles:
1. Context assembly (RAG chunks + learner profile + mastery)
2. Streaming responses via Gemini
3. Citation extraction from AI responses
4. Conversation management (create, list, get messages)
5. Unsupported question detection
"""

import re
import json
from typing import AsyncGenerator

from app.core.database.supabase import get_supabase
from app.core.ai.gemini import generate_text_stream, generate_text
from app.core.ai.rag import retrieve_context, format_context_for_prompt
from app.core.ai.prompts.tutor import (
    build_tutor_system_prompt,
    build_learner_context_string,
    build_mastery_summary_string,
)
from app.core.events.logger import log_event
from app.core.cache.redis import cache_get, cache_set, make_cache_key
from app.core.exceptions import NotFoundError


async def chat(
    project_id: str,
    user_id: str,
    message: str,
    conversation_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    Process a user message and stream the AI Tutor response.

    This is the main tutor function. It:
    1. Creates or retrieves the conversation
    2. Retrieves relevant context (RAG)
    3. Assembles the full prompt with learner context
    4. Streams the AI response
    5. Stores both the user message and AI response
    6. Extracts citations from the response

    Yields:
        SSE-formatted strings: "data: {json}\n\n"
    """
    db = get_supabase()

    # Step 1: Get or create conversation
    if conversation_id:
        conv = db.table("conversations") \
            .select("*") \
            .eq("id", conversation_id) \
            .eq("user_id", user_id) \
            .single() \
            .execute()
        if not conv.data:
            raise NotFoundError("Conversation", conversation_id)
    else:
        # Create new conversation
        conv_result = db.table("conversations") \
            .insert({
                "user_id": user_id,
                "project_id": project_id,
                "title": message[:50] + ("..." if len(message) > 50 else ""),
            }) \
            .execute()
        conversation_id = conv_result.data[0]["id"]

    # Save user message
    user_msg = db.table("messages") \
        .insert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": "user",
            "content": message,
        }) \
        .execute()

    # Update conversation message count
    db.table("conversations") \
        .update({"message_count": db.table("messages")
            .select("id", count="exact")
            .eq("conversation_id", conversation_id)
            .execute().count or 0}) \
        .eq("id", conversation_id) \
        .execute()

    # Step 2: Retrieve relevant context (RAG)
    chunks = await retrieve_context(
        query=message,
        project_id=project_id,
        user_id=user_id,
    )
    context_text = format_context_for_prompt(chunks)

    # Step 3: Get learner context and mastery
    project = db.table("projects") \
        .select("name, learning_goal") \
        .eq("id", project_id) \
        .single() \
        .execute()

    project_name = project.data.get("name", "Unknown") if project.data else "Unknown"
    learning_goal = project.data.get("learning_goal", "") if project.data else ""

    # Get learner context
    ctx_result = db.table("learner_context") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .eq("is_active", True) \
        .execute()
    learner_ctx = build_learner_context_string(ctx_result.data or [])

    # Get mastery
    mastery_result = db.table("concept_mastery") \
        .select("*, concepts(name)") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    mastery_items = []
    for m in (mastery_result.data or []):
        name = m.get("concepts", {}).get("name", "Unknown") if m.get("concepts") else "Unknown"
        mastery_items.append({
            "name": name,
            "mastery_score": m["mastery_score"],
            "trend": m["trend"],
        })
    mastery_text = build_mastery_summary_string(mastery_items)

    # Get recent conversation history (last 10 messages)
    history_result = db.table("messages") \
        .select("role, content") \
        .eq("conversation_id", conversation_id) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()
    history = list(reversed(history_result.data or []))

    # Build the system prompt
    system_prompt = build_tutor_system_prompt(
        project_name=project_name,
        learning_goal=learning_goal,
        context_chunks=context_text,
        learner_context=learner_ctx,
        mastery_summary=mastery_text,
    )

    # Build the conversation for Gemini
    conversation_text = ""
    for msg in history[:-1]:  # Exclude the current message (already in prompt)
        role_label = "User" if msg["role"] == "user" else "Assistant"
        conversation_text += f"\n{role_label}: {msg['content']}\n"
    conversation_text += f"\nUser: {message}\n"

    # Step 4: Stream the AI response
    full_response = ""

    # Send conversation_id first
    yield f"data: {json.dumps({'type': 'conversation_id', 'conversation_id': conversation_id})}\n\n"

    async for chunk in generate_text_stream(
        prompt=conversation_text,
        system_prompt=system_prompt,
        temperature=0.7,
        user_id=user_id,
        project_id=project_id,
        feature="tutor",
    ):
        full_response += chunk
        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

    # Step 5: Save AI response
    citations = _extract_citations(full_response, chunks)

    ai_msg = db.table("messages") \
        .insert({
            "conversation_id": conversation_id,
            "user_id": user_id,
            "role": "assistant",
            "content": full_response,
            "citations": [c.__dict__ if hasattr(c, '__dict__') else c for c in citations],
        }) \
        .execute()

    # Send citations
    yield f"data: {json.dumps({'type': 'citations', 'citations': citations})}\n\n"

    # Generate suggested follow-up questions
    suggestions = _generate_suggestions(message, full_response)
    yield f"data: {json.dumps({'type': 'suggestions', 'suggestions': suggestions})}\n\n"

    # Done signal
    yield f"data: {json.dumps({'type': 'done'})}\n\n"

    # Log the event
    await log_event(
        user_id=user_id,
        event_type="tutor_message_sent",
        event_data={"conversation_id": conversation_id},
        project_id=project_id,
    )


async def list_conversations(project_id: str, user_id: str) -> dict:
    """List all conversations for a project."""
    db = get_supabase()

    result = db.table("conversations") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("updated_at", desc=True) \
        .execute()

    return {"items": result.data or [], "total": len(result.data or [])}


async def get_conversation_messages(
    conversation_id: str,
    user_id: str,
) -> dict:
    """Get all messages in a conversation."""
    db = get_supabase()

    # Verify ownership
    conv = db.table("conversations") \
        .select("*") \
        .eq("id", conversation_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not conv.data:
        raise NotFoundError("Conversation", conversation_id)

    messages = db.table("messages") \
        .select("*") \
        .eq("conversation_id", conversation_id) \
        .order("created_at") \
        .execute()

    return {
        "conversation": conv.data,
        "messages": messages.data or [],
    }


# ── Private Helpers ──

def _extract_citations(response: str, chunks) -> list[dict]:
    """
    Extract source citations from the AI response.
    Looks for patterns like [Source: filename — Page X]
    """
    citations = []
    # Match [Source: ...] patterns
    pattern = r'\[Source:\s*(.+?)(?:\s*[—-]\s*Page\s*(\d+))?\]'
    matches = re.findall(pattern, response)

    seen = set()
    for file_name, page_str in matches:
        file_name = file_name.strip()
        page_num = int(page_str) if page_str else None
        key = f"{file_name}:{page_num}"

        if key not in seen:
            seen.add(key)
            # Try to find the matching chunk
            chunk_id = None
            for chunk in chunks:
                if chunk.file_name == file_name and chunk.page_number == page_num:
                    chunk_id = chunk.chunk_id
                    break

            citations.append({
                "file_name": file_name,
                "page_number": page_num,
                "chunk_id": chunk_id,
            })

    return citations


def _generate_suggestions(user_message: str, ai_response: str) -> list[str]:
    """
    Generate suggested follow-up questions based on the conversation.
    Uses simple heuristics rather than another AI call for speed.
    """
    suggestions = []

    # Check if the response mentions concepts
    if "mastery" in ai_response.lower() or "concept" in ai_response.lower():
        suggestions.append("Can you explain this in a different way?")

    if len(ai_response) > 500:
        suggestions.append("Can you summarize the key points?")

    if "example" not in ai_response.lower():
        suggestions.append("Can you give me an example?")

    if not suggestions:
        suggestions = [
            "Tell me more about this topic",
            "What should I focus on next?",
            "Quiz me on this concept",
        ]

    return suggestions[:3]
