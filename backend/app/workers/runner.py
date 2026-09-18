"""
Background Workers — Job Runner

Polls the background_jobs table and dispatches jobs to their handlers.
Runs as a separate process (or can be triggered by Supabase Edge Functions).

Job Types:
- process_material: Document processing pipeline
- post_quiz_workflow: Mastery updates + recommendation generation
- detect_repeated_mistakes: Pattern detection in quiz answers
"""

import asyncio
import traceback
from datetime import datetime, timezone
from app.core.database.supabase import get_supabase


async def run_worker(poll_interval: int = 5, max_jobs: int = 3):
    """
    Main worker loop. Polls for queued jobs and processes them.

    Args:
        poll_interval: Seconds between polls
        max_jobs: Max concurrent jobs to process
    """
    print(f"[Worker] Starting background worker (poll={poll_interval}s)")

    while True:
        try:
            await _process_pending_jobs(max_jobs)
        except Exception as e:
            print(f"[Worker] Error in poll cycle: {e}")

        await asyncio.sleep(poll_interval)


async def _process_pending_jobs(max_jobs: int = 3):
    """Fetch and process pending jobs."""
    db = get_supabase()

    # Get queued jobs ordered by priority
    result = db.table("background_jobs") \
        .select("*") \
        .eq("status", "queued") \
        .order("priority") \
        .order("created_at") \
        .limit(max_jobs) \
        .execute()

    for job in (result.data or []):
        await _execute_job(job)

    # Also check for retry-eligible jobs
    retry_result = db.table("background_jobs") \
        .select("*") \
        .eq("status", "retrying") \
        .lte("next_retry_at", datetime.now(timezone.utc).isoformat()) \
        .limit(max_jobs) \
        .execute()

    for job in (retry_result.data or []):
        await _execute_job(job)


async def _execute_job(job: dict):
    """Execute a single background job."""
    db = get_supabase()
    job_id = job["id"]

    # Mark as processing
    db.table("background_jobs").update({
        "status": "processing",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "attempts": job["attempts"] + 1,
    }).eq("id", job_id).execute()

    try:
        handler = _get_handler(job["job_type"])
        if not handler:
            raise ValueError(f"Unknown job type: {job['job_type']}")

        await handler(job["payload"], job.get("user_id"))

        # Mark as completed
        db.table("background_jobs").update({
            "status": "completed",
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", job_id).execute()

        print(f"[Worker] Job {job_id} ({job['job_type']}) completed")

    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        attempts = job["attempts"] + 1

        if attempts < job["max_attempts"]:
            # Schedule retry with exponential backoff
            retry_delay = min(300, 30 * (2 ** (attempts - 1)))  # 30s, 60s, 120s, max 5min
            from datetime import timedelta
            next_retry = datetime.now(timezone.utc) + timedelta(seconds=retry_delay)

            db.table("background_jobs").update({
                "status": "retrying",
                "error_message": error_msg[:500],
                "next_retry_at": next_retry.isoformat(),
            }).eq("id", job_id).execute()

            print(f"[Worker] Job {job_id} failed, retrying in {retry_delay}s")
        else:
            # Max retries exceeded
            db.table("background_jobs").update({
                "status": "failed",
                "error_message": error_msg[:500],
            }).eq("id", job_id).execute()

            print(f"[Worker] Job {job_id} FAILED permanently: {str(e)[:100]}")


def _get_handler(job_type: str):
    """Get the handler function for a job type."""
    handlers = {
        "process_material": _handle_process_material,
        "post_quiz_workflow": _handle_post_quiz_workflow,
        "detect_repeated_mistakes": _handle_detect_mistakes,
    }
    return handlers.get(job_type)


# ── Job Handlers ──

async def _handle_process_material(payload: dict, user_id: str | None):
    """Handle document processing job."""
    from app.features.materials.processor import process_material

    await process_material(
        material_id=payload["material_id"],
        project_id=payload["project_id"],
        user_id=user_id or payload.get("user_id", ""),
        storage_path=payload["storage_path"],
        file_name=payload["file_name"],
    )


async def _handle_post_quiz_workflow(payload: dict, user_id: str | None):
    """
    Post-quiz workflow:
    1. Update mastery scores for each concept tested
    2. Detect repeated mistakes
    3. Generate new recommendations
    """
    from app.features.mastery.service import update_mastery
    from app.features.recommendations.service import generate_recommendations

    db = get_supabase()
    quiz_id = payload["quiz_id"]
    project_id = payload["project_id"]

    # Get quiz questions with answers
    questions = db.table("quiz_questions") \
        .select("concept_id, is_correct, score") \
        .eq("quiz_id", quiz_id) \
        .execute()

    # Update mastery for each concept
    for q in (questions.data or []):
        if q.get("concept_id"):
            await update_mastery(
                user_id=user_id or "",
                project_id=project_id,
                concept_id=q["concept_id"],
                is_correct=q.get("is_correct", False),
                quiz_id=quiz_id,
            )

    # Detect repeated mistakes
    await _detect_repeated_mistakes(user_id or "", project_id)

    # Generate recommendations
    try:
        await generate_recommendations(project_id, user_id or "")
    except Exception as e:
        print(f"[Worker] Recommendation generation failed: {e}")


async def _handle_detect_mistakes(payload: dict, user_id: str | None):
    """Standalone repeated mistake detection."""
    await _detect_repeated_mistakes(
        user_id or payload.get("user_id", ""),
        payload["project_id"],
    )


async def _detect_repeated_mistakes(user_id: str, project_id: str):
    """
    Detect repeated mistakes: concepts where the user has gotten
    3+ incorrect answers in the last 5 attempts.
    """
    db = get_supabase()

    # Get concepts with recent incorrect answers
    mastery = db.table("concept_mastery") \
        .select("concept_id, incorrect_count, quiz_attempts, concepts(name)") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .gte("incorrect_count", 3) \
        .execute()

    for m in (mastery.data or []):
        concept_name = m.get("concepts", {}).get("name", "") if m.get("concepts") else ""
        incorrect_ratio = m["incorrect_count"] / max(1, m["quiz_attempts"])

        if incorrect_ratio >= 0.5:  # 50%+ incorrect
            # Check if we already have this as a repeated mistake
            existing = db.table("learner_context") \
                .select("id") \
                .eq("user_id", user_id) \
                .eq("project_id", project_id) \
                .eq("context_type", "repeated_mistake") \
                .eq("concept_id", m["concept_id"]) \
                .eq("is_active", True) \
                .execute()

            if not existing.data:
                content = (
                    f"Repeatedly struggles with '{concept_name}' — "
                    f"{m['incorrect_count']}/{m['quiz_attempts']} incorrect "
                    f"({incorrect_ratio*100:.0f}% error rate)"
                )
                db.table("learner_context").insert({
                    "user_id": user_id,
                    "project_id": project_id,
                    "context_type": "repeated_mistake",
                    "content": content,
                    "source": "system",
                    "concept_id": m["concept_id"],
                }).execute()

                from app.core.events.logger import log_event
                await log_event(
                    user_id=user_id,
                    event_type="repeated_mistake_detected",
                    event_data={"concept": concept_name},
                    project_id=project_id,
                )


# ── Entry Point ──

if __name__ == "__main__":
    asyncio.run(run_worker())
