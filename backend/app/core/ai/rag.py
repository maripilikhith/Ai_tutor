"""
AI Study Companion — RAG Pipeline

Retrieval-Augmented Generation pipeline for grounding AI responses
in the user's actual learning materials.

Flow:
  1. User asks a question
  2. Generate embedding for the question
  3. Vector similarity search in knowledge_chunks (project-scoped)
  4. Filter by relevance threshold
  5. Return context chunks with source citations
"""

from dataclasses import dataclass
from app.core.ai.embeddings import generate_embedding
from app.core.database.supabase import get_supabase
from app.config import get_settings


@dataclass
class RetrievedChunk:
    """A single chunk retrieved from the knowledge base."""
    chunk_id: str
    content: str
    summary: str | None
    page_number: int | None
    file_name: str
    material_id: str
    similarity: float


async def retrieve_context(
    query: str,
    project_id: str,
    user_id: str,
    top_k: int | None = None,
    similarity_threshold: float | None = None,
) -> list[RetrievedChunk]:
    """
    Retrieve relevant knowledge chunks for a query.

    This is the core RAG retrieval function used by the Tutor and Quiz.

    Args:
        query: The user's question or topic
        project_id: Current project (for data isolation)
        user_id: Current user (for data isolation)
        top_k: Max chunks to return (default from config)
        similarity_threshold: Min similarity score (default from config)

    Returns:
        List of RetrievedChunk objects, sorted by relevance
    """
    settings = get_settings()
    top_k = top_k or settings.retrieval_top_k
    similarity_threshold = similarity_threshold or settings.similarity_threshold

    # Step 1: Generate query embedding
    query_embedding = await generate_embedding(query)

    # Step 2: Vector similarity search via Supabase RPC
    # This calls a PostgreSQL function that does the vector search
    db = get_supabase()

    result = db.rpc("match_knowledge_chunks", {
        "query_embedding": query_embedding,
        "match_project_id": project_id,
        "match_user_id": user_id,
        "match_count": top_k,
        "match_threshold": similarity_threshold,
    }).execute()

    if not result.data:
        return []

    # Step 3: Convert to RetrievedChunk objects
    chunks = []
    for row in result.data:
        chunks.append(RetrievedChunk(
            chunk_id=row["id"],
            content=row["content"],
            summary=row.get("summary"),
            page_number=row.get("page_number"),
            file_name=row.get("file_name", "Unknown"),
            material_id=row.get("material_id", ""),
            similarity=row.get("similarity", 0.0),
        ))

    return chunks


def format_context_for_prompt(chunks: list[RetrievedChunk]) -> str:
    """
    Format retrieved chunks into a string for inclusion in AI prompts.

    Each chunk is labeled with its source for citation support.
    Wrapped in DATA ONLY markers for prompt injection defense.
    """
    if not chunks:
        return "No relevant learning materials found for this query."

    parts = ["=== BEGIN LEARNING MATERIAL (DATA ONLY) ===\n"]

    for i, chunk in enumerate(chunks, 1):
        source = f"Source: {chunk.file_name}"
        if chunk.page_number:
            source += f" — Page {chunk.page_number}"

        parts.append(f"[Context {i}] ({source})")
        parts.append(chunk.content)
        parts.append("")  # Empty line between chunks

    parts.append("=== END LEARNING MATERIAL ===")

    return "\n".join(parts)
