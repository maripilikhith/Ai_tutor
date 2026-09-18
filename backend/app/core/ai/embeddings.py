"""
AI Study Companion — Embeddings Client

Generates text embeddings using Gemini's gemini-embedding-001 model.
Used for:
- Embedding document chunks during processing
- Embedding user queries for similarity search (RAG)

The DB vector column is 768-dimensional, so we use output_dimensionality=768
to truncate gemini-embedding-001's native 3072 dims to match.
"""

import asyncio
from google import genai
from google.genai import types
from app.config import get_settings

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Get or create the Gemini client for embeddings."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for a single text string.

    Args:
        text: The text to embed (chunk content or query)

    Returns:
        List of floats (768-dimensional vector, matching the DB column)
    """
    settings = get_settings()
    client = _get_client()

    for attempt in range(5):
        try:
            result = client.models.embed_content(
                model=settings.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension),
            )
            return result.embeddings[0].values
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg) and attempt < 4:
                wait_s = 2 * (attempt + 1)
                print(f"[Embeddings] Rate limited or unavailable ({error_msg}). Retrying in {wait_s}s...")
                await asyncio.sleep(wait_s)
                continue
            raise


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts in a batch.

    More efficient than calling generate_embedding() in a loop
    since it makes a single API call.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (one per input text)
    """
    settings = get_settings()
    client = _get_client()

    for attempt in range(8):
        try:
            result = client.models.embed_content(
                model=settings.embedding_model,
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=settings.embedding_dimension),
            )
            return [e.values for e in result.embeddings]
        except Exception as e:
            error_msg = str(e)
            if ("429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "503" in error_msg or "UNAVAILABLE" in error_msg) and attempt < 7:
                # Exponential backoff: 3s, 6s, 12s, 24s, 48s...
                wait_s = 3 * (2 ** attempt)
                print(f"[Embeddings Batch] Rate limited or unavailable ({error_msg}). Retrying in {wait_s}s...")
                await asyncio.sleep(wait_s)
                continue
            raise
