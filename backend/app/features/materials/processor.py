"""
Materials Feature — Document Processing Pipeline

The core document processing pipeline:
  PDF → PyMuPDF (pages) → Gemini Vision (extract) → Chunk → Embed → Store

This runs as a background job, triggered when a user uploads a PDF.
"""

import asyncio
import io
import json
import fitz  # PyMuPDF
from app.core.database.supabase import get_supabase
from app.core.storage.supabase_storage import download_file
from app.core.ai.gemini import generate_vision, generate_text, generate_structured
from app.core.ai.embeddings import generate_embedding, generate_embeddings_batch
from app.core.ai.prompts.extraction import build_extraction_prompt
from app.core.events.logger import log_event
from app.config import get_settings


async def process_material(
    material_id: str,
    project_id: str,
    user_id: str,
    storage_path: str,
    file_name: str,
) -> None:
    """
    Full document processing pipeline.

    Steps:
    1. Download PDF from storage
    2. Convert pages to images (PyMuPDF)
    3. Extract text + concepts from each page (Gemini Vision)
    4. Chunk the extracted text
    5. Generate embeddings for each chunk
    6. Store chunks + embeddings in knowledge_chunks
    7. Extract + deduplicate concepts
    8. Update material status to 'ready'
    """
    db = get_supabase()

    try:
        # Update status to processing
        db.table("materials") \
            .update({"status": "processing"}) \
            .eq("id", material_id) \
            .execute()

        # Step 1: Download PDF
        pdf_bytes = await download_file(storage_path)

        # Step 2: Convert pages to images
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)

        # Update page count
        db.table("materials") \
            .update({"page_count": page_count}) \
            .eq("id", material_id) \
            .execute()

        # Step 3: Extract text from each page (Direct text fast-path + Vision fallback)
        all_text = ""
        all_concepts = []

        for page_num in range(page_count):
            page = doc[page_num]

            # Fast-path: Check if PDF page has embedded text
            direct_text = page.get_text().strip()
            if len(direct_text) > 40:
                all_text += f"\n\n--- Page {page_num + 1} ---\n\n{direct_text}"
                continue

            # Fallback to Gemini Vision only for scanned / image pages
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("png")
                prompt = build_extraction_prompt(page_num + 1, page_count)

                extraction_result = await generate_vision(
                    images=[img_bytes],
                    prompt=prompt,
                    user_id=user_id,
                    project_id=project_id,
                )

                parsed = _parse_extraction(extraction_result)
                page_text = parsed.get("text_content", "")
                if page_text:
                    all_text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"

            except Exception as e:
                print(f"Warning: Failed to process page {page_num + 1}: {e}")
                if direct_text:
                    all_text += f"\n\n--- Page {page_num + 1} ---\n\n{direct_text}"

        doc.close()

        # Step 3.5: Extract high-level overarching concepts in one structured call
        if all_text.strip():
            try:
                from pydantic import BaseModel, Field

                class ConceptItem(BaseModel):
                    name: str = Field(description="Concept name")
                    description: str = Field(description="Brief explanation of the concept")

                class DocumentConcepts(BaseModel):
                    concepts: list[ConceptItem] = Field(description="Key concepts extracted from the material")

                sample_text = all_text[:20000] # Give it enough context to find broad topics
                extracted_doc_concepts = await generate_structured(
                    prompt=f"Extract 5 to 15 high-level, overarching topics from this study material. Do NOT extract overly specific or granular sub-topics. Group concepts into broad themes.\n\nMaterial:\n\n{sample_text}",
                    response_schema=DocumentConcepts,
                    user_id=user_id,
                    project_id=project_id,
                    feature="concept_extraction",
                )
                for c in extracted_doc_concepts.concepts:
                    all_concepts.append({"name": c.name, "description": c.description})
            except Exception as ce:
                print(f"Warning: Failed to extract document concepts: {ce}")

        # Step 4: Chunk the extracted text
        settings = get_settings()
        chunks = _chunk_text(
            all_text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
        )

        # Step 5 & 6: Generate embeddings and store chunks
        if chunks:
            # Batch embed for efficiency
            chunk_texts = [c["content"] for c in chunks]

            # Process in batches of 20 to avoid API limits
            batch_size = 20
            all_embeddings = []
            for i in range(0, len(chunk_texts), batch_size):
                batch = chunk_texts[i:i + batch_size]
                embeddings = await generate_embeddings_batch(batch)
                all_embeddings.extend(embeddings)
                if i + batch_size < len(chunk_texts):
                    await asyncio.sleep(3.0)

            # Store chunks with embeddings
            chunk_records = []
            for i, chunk in enumerate(chunks):
                chunk_records.append({
                    "user_id": user_id,
                    "project_id": project_id,
                    "material_id": material_id,
                    "content": chunk["content"],
                    "summary": chunk.get("summary", ""),
                    "page_number": chunk.get("page_number"),
                    "chunk_index": i,
                    "file_name": file_name,
                    "token_count": len(chunk["content"].split()),
                    "embedding": all_embeddings[i] if i < len(all_embeddings) else None,
                })

            # Insert in batches
            for i in range(0, len(chunk_records), 50):
                batch = chunk_records[i:i + 50]
                db.table("knowledge_chunks").insert(batch).execute()

        # Step 7: Extract and deduplicate concepts, then seed mastery at 0%
        newly_stored_ids = await _store_concepts(all_concepts, project_id, user_id, material_id)
        if newly_stored_ids:
            await _seed_mastery(newly_stored_ids, project_id, user_id)

        # Step 8: Update material status
        db.table("materials") \
            .update({
                "status": "ready",
                "processed_at": "now()",
            }) \
            .eq("id", material_id) \
            .execute()

        await log_event(
            user_id=user_id,
            event_type="material_processed",
            event_data={
                "file_name": file_name,
                "page_count": page_count,
                "chunks_created": len(chunks),
                "concepts_extracted": len(all_concepts),
            },
            project_id=project_id,
        )

    except Exception as e:
        # Mark as failed
        db.table("materials") \
            .update({
                "status": "failed",
                "error_message": str(e)[:500],
            }) \
            .eq("id", material_id) \
            .execute()

        await log_event(
            user_id=user_id,
            event_type="material_failed",
            event_data={"file_name": file_name, "error": str(e)[:200]},
            project_id=project_id,
        )

        raise


def _chunk_text(
    text: str,
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[dict]:
    """
    Split text into overlapping chunks.

    Uses sentence-aware splitting to avoid breaking mid-sentence.
    Each chunk includes the page number it came from.
    """
    if not text.strip():
        return []

    # Split into sentences (rough approximation)
    sentences = []
    current_page = 1

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Track page numbers
        if line.startswith("--- Page ") and line.endswith("---"):
            try:
                current_page = int(line.replace("--- Page ", "").replace(" ---", ""))
            except ValueError:
                pass
            continue

        # Split line into sentences
        for sent in _split_sentences(line):
            if sent.strip():
                sentences.append({"text": sent.strip(), "page": current_page})

    if not sentences:
        return []

    # Build chunks from sentences
    chunks = []
    current_chunk_texts = []
    current_chunk_words = 0
    chunk_page = sentences[0]["page"]

    for sent in sentences:
        sent_words = len(sent["text"].split())

        if current_chunk_words + sent_words > chunk_size and current_chunk_texts:
            # Save current chunk
            chunks.append({
                "content": " ".join(current_chunk_texts),
                "page_number": chunk_page,
            })

            # Start new chunk with overlap
            overlap_words = 0
            overlap_start = len(current_chunk_texts)
            for j in range(len(current_chunk_texts) - 1, -1, -1):
                overlap_words += len(current_chunk_texts[j].split())
                if overlap_words >= overlap:
                    overlap_start = j
                    break

            current_chunk_texts = current_chunk_texts[overlap_start:]
            current_chunk_words = sum(len(t.split()) for t in current_chunk_texts)
            chunk_page = sent["page"]

        current_chunk_texts.append(sent["text"])
        current_chunk_words += sent_words

    # Don't forget the last chunk
    if current_chunk_texts:
        chunks.append({
            "content": " ".join(current_chunk_texts),
            "page_number": chunk_page,
        })

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Simple sentence splitter. Splits on period + space patterns."""
    import re
    # Split on sentence-ending punctuation followed by space or end
    parts = re.split(r'(?<=[.!?])\s+', text)
    return [p for p in parts if p.strip()]


def _parse_extraction(result_text: str) -> dict:
    """Parse the JSON extraction result from Gemini Vision."""
    try:
        # Try direct JSON parse
        return json.loads(result_text)
    except json.JSONDecodeError:
        # Try to extract JSON from markdown code blocks
        if "```json" in result_text:
            json_str = result_text.split("```json")[1].split("```")[0]
            return json.loads(json_str)
        elif "```" in result_text:
            json_str = result_text.split("```")[1].split("```")[0]
            return json.loads(json_str)
        else:
            # Return just the text content
            return {"text_content": result_text, "key_concepts": []}


async def _store_concepts(
    concepts: list[dict],
    project_id: str,
    user_id: str,
    material_id: str,
) -> list[str]:
    """
    Store extracted concepts, deduplicating by name within the project.
    Returns the list of newly inserted concept IDs.
    """
    if not concepts:
        return []

    db = get_supabase()

    # Get existing concepts for this project
    existing = db.table("concepts") \
        .select("name") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    existing_names = {c["name"].lower() for c in (existing.data or [])}
    newly_inserted_ids = []

    # Insert new concepts
    for concept in concepts:
        name = concept.get("name", "").strip()
        if not name or name.lower() in existing_names:
            continue

        try:
            result = db.table("concepts").insert({
                "user_id": user_id,
                "project_id": project_id,
                "name": name,
                "description": concept.get("description", ""),
                "material_ids": [material_id],
            }).execute()
            if result.data:
                newly_inserted_ids.append(result.data[0]["id"])
            existing_names.add(name.lower())
        except Exception:
            # Skip duplicates (UNIQUE constraint)
            pass

    return newly_inserted_ids


async def _seed_mastery(
    concept_ids: list[str],
    project_id: str,
    user_id: str,
) -> None:
    """
    Create concept_mastery rows at score=0 for each new concept.

    This ensures the Mastery page shows all topics from the moment
    a PDF is processed, not just after a quiz is taken.
    Skips concepts that already have a mastery row (UNIQUE constraint).
    """
    db = get_supabase()

    for concept_id in concept_ids:
        try:
            db.table("concept_mastery").insert({
                "user_id": user_id,
                "project_id": project_id,
                "concept_id": concept_id,
                "mastery_score": 0.0,
                "quiz_attempts": 0,
                "correct_count": 0,
                "incorrect_count": 0,
                "trend": "new",
            }).execute()
        except Exception:
            # Already exists — skip (UNIQUE constraint on user+project+concept)
            pass
