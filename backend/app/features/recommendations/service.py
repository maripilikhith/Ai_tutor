"""
Recommendations Feature — Business Logic

AI-generated learning recommendations based on mastery, quiz history, and patterns.
"""

from pydantic import BaseModel, Field
from app.core.database.supabase import get_supabase
from app.core.ai.gemini import generate_structured
from app.core.ai.prompts.recommendation import build_recommendation_prompt
from app.core.events.logger import log_event
from app.core.exceptions import NotFoundError


class RecommendationItem(BaseModel):
    type: str
    title: str
    description: str
    priority: str
    related_concepts: list[str]
    related_materials: list[str]


class RecommendationSet(BaseModel):
    recommendations: list[RecommendationItem]


async def get_recommendations(project_id: str, user_id: str) -> dict:
    """Get active recommendations for a project."""
    db = get_supabase()

    result = db.table("recommendations") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .eq("status", "active") \
        .order("created_at", desc=True) \
        .execute()

    return {"items": result.data or [], "total": len(result.data or [])}


async def generate_recommendations(project_id: str, user_id: str) -> list[dict]:
    """Generate new AI recommendations based on current learning state."""
    db = get_supabase()

    # Gather context
    project = db.table("projects") \
        .select("learning_goal") \
        .eq("id", project_id).single().execute()
    learning_goal = project.data.get("learning_goal", "") if project.data else ""

    mastery = db.table("concept_mastery") \
        .select("mastery_score, trend, concepts(name)") \
        .eq("project_id", project_id).eq("user_id", user_id).execute()

    mastery_lines = []
    for m in (mastery.data or []):
        name = m.get("concepts", {}).get("name", "?") if m.get("concepts") else "?"
        mastery_lines.append(f"{name}: {m['mastery_score']:.0f}% ({m['trend']})")

    quizzes = db.table("quizzes") \
        .select("score_percentage, completed_at") \
        .eq("project_id", project_id).eq("user_id", user_id) \
        .eq("status", "completed") \
        .order("completed_at", desc=True).limit(5).execute()

    quiz_lines = [f"{q['score_percentage']:.0f}% on {q['completed_at'][:10]}" for q in (quizzes.data or [])]

    mistakes = db.table("learner_context") \
        .select("content") \
        .eq("project_id", project_id).eq("user_id", user_id) \
        .eq("context_type", "repeated_mistake") \
        .eq("is_active", True).execute()
    mistake_lines = [m["content"] for m in (mistakes.data or [])]

    previous = db.table("recommendations") \
        .select("title") \
        .eq("project_id", project_id).eq("user_id", user_id) \
        .order("created_at", desc=True).limit(10).execute()
    prev_lines = [r["title"] for r in (previous.data or [])]

    materials = db.table("materials") \
        .select("file_name") \
        .eq("project_id", project_id).eq("status", "ready").execute()
    mat_lines = [m["file_name"] for m in (materials.data or [])]

    prompt = build_recommendation_prompt(
        learning_goal=learning_goal,
        mastery_summary="\n".join(mastery_lines) or "No mastery data",
        recent_quiz_results="\n".join(quiz_lines) or "No quizzes taken",
        growth_trends="See mastery data above",
        repeated_mistakes="\n".join(mistake_lines) or "None detected",
        previous_recommendations="\n".join(prev_lines) or "None",
        available_materials="\n".join(mat_lines) or "No materials",
    )

    result = await generate_structured(
        prompt=prompt,
        response_schema=RecommendationSet,
        system_prompt="Generate actionable learning recommendations.",
        temperature=0.5,
        user_id=user_id,
        project_id=project_id,
        feature="recommendations",
    )

    # Store recommendations
    created = []
    for rec in result.recommendations:
        row = db.table("recommendations").insert({
            "user_id": user_id,
            "project_id": project_id,
            "type": rec.type,
            "title": rec.title,
            "description": rec.description,
            "priority": rec.priority,
            "related_concepts": rec.related_concepts,
            "related_materials": rec.related_materials,
        }).execute()
        created.append(row.data[0])

    await log_event(
        user_id=user_id,
        event_type="recommendation_generated",
        event_data={"count": len(created)},
        project_id=project_id,
    )

    return created


async def update_recommendation(rec_id: str, user_id: str, status: str) -> dict:
    """Update a recommendation's status (completed/dismissed)."""
    db = get_supabase()

    result = db.table("recommendations") \
        .update({"status": status}) \
        .eq("id", rec_id).eq("user_id", user_id).execute()

    if not result.data:
        raise NotFoundError("Recommendation", rec_id)

    event_type = f"recommendation_{status}"
    await log_event(user_id=user_id, event_type=event_type, event_data={"rec_id": rec_id})

    return result.data[0]
