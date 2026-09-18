"""
Mastery Feature — Business Logic

Handles mastery tracking, updates, and growth data.

Update Algorithm (from blueprint §15):
- Correct answer: score + 15% * (1 - score/100) [diminishing returns]
- Incorrect answer: score - 10%
- Score clamped to [0, 100]
- Trend calculated from last 3 quizzes
"""

from app.core.database.supabase import get_supabase
from app.core.exceptions import NotFoundError


async def get_mastery(project_id: str, user_id: str) -> dict:
    """Get all concept mastery scores for a project."""
    db = get_supabase()

    result = db.table("concept_mastery") \
        .select("*, concepts(name, description)") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("mastery_score", desc=True) \
        .execute()

    items = []
    for m in (result.data or []):
        concept = m.get("concepts", {}) or {}
        items.append({
            **m,
            "concept_name": concept.get("name", "Unknown"),
        })

    scores = [m["mastery_score"] for m in items]
    avg = round(sum(scores) / len(scores), 1) if scores else 0.0

    return {"items": items, "total": len(items), "avg_mastery": avg}


async def get_growth_data(project_id: str, user_id: str) -> dict:
    """Get mastery history for growth charts."""
    db = get_supabase()

    result = db.table("mastery_history") \
        .select("mastery_score, recorded_at, concepts(name)") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("recorded_at") \
        .execute()

    data_points = []
    concept_names = set()

    for row in (result.data or []):
        name = row.get("concepts", {}).get("name", "Unknown") if row.get("concepts") else "Unknown"
        concept_names.add(name)
        data_points.append({
            "date": row["recorded_at"][:10],
            "concept_name": name,
            "mastery_score": row["mastery_score"],
        })

    return {
        "data_points": data_points,
        "concepts": list(concept_names),
    }


async def update_mastery(
    user_id: str,
    project_id: str,
    concept_id: str,
    is_correct: bool,
    quiz_id: str | None = None,
) -> dict:
    """
    Update mastery score after a quiz answer.

    Algorithm:
    - Correct: score + 15 * (1 - score/100)  → diminishing returns at high mastery
    - Incorrect: score - 10                    → flat penalty
    - Clamped to [0, 100]
    """
    db = get_supabase()

    # Get or create mastery record
    result = db.table("concept_mastery") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("project_id", project_id) \
        .eq("concept_id", concept_id) \
        .execute()

    if result.data:
        mastery = result.data[0]
        old_score = mastery["mastery_score"]
        attempts = mastery["quiz_attempts"]
        correct = mastery["correct_count"]
        incorrect = mastery["incorrect_count"]
    else:
        old_score = 0.0
        attempts = 0
        correct = 0
        incorrect = 0

    # Calculate new score
    if is_correct:
        delta = 15 * (1 - old_score / 100)
        new_score = min(100, old_score + delta)
        correct += 1
    else:
        new_score = max(0, old_score - 10)
        incorrect += 1

    new_score = round(new_score, 1)
    attempts += 1

    # Calculate trend from recent history
    trend = await _calculate_trend(user_id, project_id, concept_id, new_score)

    # Upsert mastery record
    mastery_data = {
        "user_id": user_id,
        "project_id": project_id,
        "concept_id": concept_id,
        "mastery_score": new_score,
        "quiz_attempts": attempts,
        "correct_count": correct,
        "incorrect_count": incorrect,
        "trend": trend,
        "last_tested_at": "now()",
    }

    if result.data:
        db.table("concept_mastery") \
            .update(mastery_data) \
            .eq("id", result.data[0]["id"]) \
            .execute()
    else:
        db.table("concept_mastery").insert(mastery_data).execute()

    # Record history snapshot for growth charts
    db.table("mastery_history").insert({
        "user_id": user_id,
        "project_id": project_id,
        "concept_id": concept_id,
        "mastery_score": new_score,
        "quiz_id": quiz_id,
    }).execute()

    return {
        "concept_id": concept_id,
        "old_score": old_score,
        "new_score": new_score,
        "trend": trend,
    }


async def _calculate_trend(
    user_id: str,
    project_id: str,
    concept_id: str,
    current_score: float,
) -> str:
    """Calculate mastery trend from recent history."""
    db = get_supabase()

    history = db.table("mastery_history") \
        .select("mastery_score") \
        .eq("user_id", user_id) \
        .eq("project_id", project_id) \
        .eq("concept_id", concept_id) \
        .order("recorded_at", desc=True) \
        .limit(3) \
        .execute()

    scores = [h["mastery_score"] for h in (history.data or [])]

    if len(scores) < 2:
        return "new"

    # Compare recent scores
    recent_avg = sum(scores[:2]) / 2
    older_avg = sum(scores[1:]) / len(scores[1:])

    if recent_avg > older_avg + 5:
        return "improving"
    elif recent_avg < older_avg - 5:
        return "declining"
    else:
        return "stable"
