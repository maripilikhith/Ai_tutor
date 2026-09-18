"""
Projects Feature — Business Logic

CRUD operations for projects + dashboard data assembly.
"""

from app.core.database.supabase import get_supabase
from app.core.events.logger import log_event
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.auth.permissions import check_ownership


async def list_projects(user_id: str, space_id: str | None = None) -> dict:
    """
    List projects, optionally filtered by space.

    Args:
        user_id: Current user
        space_id: Optional space filter

    Returns:
        { items: [...], total: int }
    """
    db = get_supabase()

    query = db.table("projects") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("created_at", desc=False)

    if space_id:
        query = query.eq("space_id", space_id)

    result = query.execute()
    projects = result.data or []

    # Enrich with stats
    for project in projects:
        project = await _enrich_project(project, user_id)

    return {"items": projects, "total": len(projects)}


async def get_project(project_id: str, user_id: str) -> dict:
    """Get a single project by ID with stats."""
    db = get_supabase()

    result = db.table("projects") \
        .select("*") \
        .eq("id", project_id) \
        .single() \
        .execute()

    project = result.data
    if not project:
        raise NotFoundError("Project", project_id)

    if not check_ownership(project["user_id"], user_id):
        raise ForbiddenError()

    return await _enrich_project(project, user_id)


async def create_project(user_id: str, data: dict) -> dict:
    """Create a new project within a space."""
    db = get_supabase()

    # Verify the space exists and belongs to the user
    space_result = db.table("spaces") \
        .select("id") \
        .eq("id", data["space_id"]) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not space_result.data:
        raise NotFoundError("Space", data["space_id"])

    result = db.table("projects") \
        .insert({
            "user_id": user_id,
            "space_id": data["space_id"],
            "name": data["name"],
            "description": data.get("description", ""),
            "learning_goal": data.get("learning_goal", ""),
        }) \
        .execute()

    project = result.data[0]
    project["material_count"] = 0
    project["quiz_count"] = 0
    project["avg_mastery"] = 0.0

    await log_event(
        user_id=user_id,
        event_type="project_created",
        event_data={"project_name": data["name"]},
        project_id=project["id"],
        space_id=data["space_id"],
    )

    # Seed initial concepts + mastery from project goal (runs in background)
    # This gives the Mastery page something to show even before a PDF is uploaded.
    import asyncio
    asyncio.create_task(
        _seed_concepts_from_goal(
            project_id=project["id"],
            user_id=user_id,
            project_name=data["name"],
            learning_goal=data.get("learning_goal", ""),
        )
    )

    return project


async def update_project(project_id: str, user_id: str, data: dict) -> dict:
    """Update a project's details."""
    await get_project(project_id, user_id)

    db = get_supabase()
    update_data = {k: v for k, v in data.items() if v is not None}

    if not update_data:
        return await get_project(project_id, user_id)

    db.table("projects") \
        .update(update_data) \
        .eq("id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    return await get_project(project_id, user_id)


async def delete_project(project_id: str, user_id: str) -> None:
    """Delete a project and all related data (cascading)."""
    await get_project(project_id, user_id)

    db = get_supabase()
    db.table("projects") \
        .delete() \
        .eq("id", project_id) \
        .eq("user_id", user_id) \
        .execute()


async def get_project_dashboard(project_id: str, user_id: str) -> dict:
    """
    Assemble the full project dashboard data.

    Includes: project details, recent activity, mastery summary,
    active recommendations, and aggregate stats.
    """
    project = await get_project(project_id, user_id)
    db = get_supabase()

    # Recent activity (last 10 events)
    activity_result = db.table("learning_events") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .limit(10) \
        .execute()

    # Mastery summary (all concepts)
    mastery_result = db.table("concept_mastery") \
        .select("*, concepts(name)") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    mastery_items = []
    for m in (mastery_result.data or []):
        concept_name = m.get("concepts", {}).get("name", "Unknown") if m.get("concepts") else "Unknown"
        mastery_items.append({
            "concept_id": m["concept_id"],
            "concept_name": concept_name,
            "mastery_score": m["mastery_score"],
            "trend": m["trend"],
            "quiz_attempts": m["quiz_attempts"],
        })

    # Active recommendations
    rec_result = db.table("recommendations") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .eq("status", "active") \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()

    # Stats
    quiz_result = db.table("quizzes") \
        .select("id, score_percentage", count="exact") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .eq("status", "completed") \
        .execute()

    conversation_count = db.table("conversations") \
        .select("id", count="exact") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    total_quizzes = quiz_result.count or 0
    quiz_scores = [q["score_percentage"] for q in (quiz_result.data or []) if q.get("score_percentage")]
    avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0

    return {
        "project": project,
        "recent_activity": activity_result.data or [],
        "mastery_summary": mastery_items,
        "recommendations": rec_result.data or [],
        "stats": {
            "material_count": project.get("material_count", 0),
            "quiz_count": total_quizzes,
            "avg_quiz_score": round(avg_quiz_score, 1),
            "conversation_count": conversation_count.count or 0,
            "avg_mastery": project.get("avg_mastery", 0),
            "concept_count": len(mastery_items),
        },
    }


# ── Private Helpers ──

async def _enrich_project(project: dict, user_id: str) -> dict:
    """Add computed stats (material_count, quiz_count, avg_mastery) to a project."""
    db = get_supabase()

    # Material count
    mat_result = db.table("materials") \
        .select("id", count="exact") \
        .eq("project_id", project["id"]) \
        .execute()
    project["material_count"] = mat_result.count or 0

    # Quiz count (completed only)
    quiz_result = db.table("quizzes") \
        .select("id", count="exact") \
        .eq("project_id", project["id"]) \
        .eq("status", "completed") \
        .execute()
    project["quiz_count"] = quiz_result.count or 0

    # Average mastery
    mastery_result = db.table("concept_mastery") \
        .select("mastery_score") \
        .eq("project_id", project["id"]) \
        .eq("user_id", user_id) \
        .execute()

    scores = [m["mastery_score"] for m in (mastery_result.data or [])]
    project["avg_mastery"] = round(sum(scores) / len(scores), 1) if scores else 0.0

    return project


async def _seed_concepts_from_goal(
    project_id: str,
    user_id: str,
    project_name: str,
    learning_goal: str,
) -> None:
    """
    Generate initial concepts from the project name + learning goal using AI.

    This is a FALLBACK for when no PDF has been uploaded yet. It gives the
    Mastery page something to display immediately after project creation.

    If a PDF is later uploaded, its concepts will be added on top (not replaced).
    Concepts already created by a PDF take priority since they are more specific.
    """
    # Skip if neither name nor goal is meaningful
    topic = learning_goal.strip() or project_name.strip()
    if not topic or len(topic) < 3:
        return

    try:
        from pydantic import BaseModel, Field
        from app.core.ai.gemini import generate_structured
        from app.core.database.supabase import get_supabase

        class ConceptItem(BaseModel):
            name: str = Field(description="Short concept name (2-5 words)")
            description: str = Field(description="One-sentence explanation of the concept")

        class StudyTopics(BaseModel):
            concepts: list[ConceptItem] = Field(
                description="Key topics/concepts a student must master for this subject"
            )

        prompt = (
            f"You are a curriculum designer. Generate 6 to 10 key study concepts "
            f"that a student must master for the following subject:\n\n"
            f"Subject: {project_name}\n"
            f"Learning Goal: {learning_goal or 'General understanding'}\n\n"
            f"Each concept should be a distinct, testable topic. "
            f"Return short concept names (2-5 words) with a one-sentence explanation."
        )

        result = await generate_structured(
            prompt=prompt,
            response_schema=StudyTopics,
            temperature=0.3,
            feature="concept_seeding",
            user_id=user_id,
            project_id=project_id,
        )

        if not result or not result.concepts:
            return

        db = get_supabase()

        # Check which concepts already exist (PDF may have run first)
        existing = db.table("concepts") \
            .select("name") \
            .eq("project_id", project_id) \
            .eq("user_id", user_id) \
            .execute()
        existing_names = {c["name"].lower() for c in (existing.data or [])}

        for c in result.concepts:
            name = c.name.strip()
            if not name or name.lower() in existing_names:
                continue

            try:
                insert_result = db.table("concepts").insert({
                    "user_id": user_id,
                    "project_id": project_id,
                    "name": name,
                    "description": c.description,
                    "material_ids": [],  # No PDF yet
                }).execute()

                if insert_result.data:
                    concept_id = insert_result.data[0]["id"]
                    # Seed mastery at 0%
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
                    existing_names.add(name.lower())

            except Exception:
                pass  # Skip duplicates silently

        print(f"[Project] Seeded {len(result.concepts)} concepts from goal for project {project_id}")

    except Exception as e:
        # Non-critical — don't crash project creation if this fails
        print(f"[Project] Warning: Failed to seed concepts from goal: {e}")
