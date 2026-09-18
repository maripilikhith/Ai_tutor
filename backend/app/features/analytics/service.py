"""
Analytics Feature — Business Logic

Assembles analytics data for project and global dashboards.
"""

from datetime import datetime, timedelta, timezone
from app.core.database.supabase import get_supabase


async def get_project_analytics(project_id: str, user_id: str) -> dict:
    """Get analytics for a single project."""
    db = get_supabase()

    # Stats
    materials = db.table("materials").select("id", count="exact") \
        .eq("project_id", project_id).eq("status", "ready").execute()
    quizzes = db.table("quizzes").select("id, score_percentage", count="exact") \
        .eq("project_id", project_id).eq("status", "completed").execute()
    conversations = db.table("conversations").select("id", count="exact") \
        .eq("project_id", project_id).execute()
    mastery = db.table("concept_mastery").select("mastery_score") \
        .eq("project_id", project_id).eq("user_id", user_id).execute()

    scores = [m["mastery_score"] for m in (mastery.data or [])]
    avg_mastery = round(sum(scores) / len(scores), 1) if scores else 0
    quiz_scores = [q["score_percentage"] for q in (quizzes.data or []) if q.get("score_percentage")]
    avg_quiz = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0

    stats = [
        {"label": "Materials", "value": materials.count or 0},
        {"label": "Quizzes Taken", "value": quizzes.count or 0},
        {"label": "Avg Quiz Score", "value": f"{avg_quiz}%"},
        {"label": "Avg Mastery", "value": f"{avg_mastery}%"},
        {"label": "Conversations", "value": conversations.count or 0},
        {"label": "Concepts", "value": len(scores)},
    ]

    # Activity over time (last 30 days)
    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    events = db.table("learning_events") \
        .select("event_type, created_at") \
        .eq("project_id", project_id).eq("user_id", user_id) \
        .gte("created_at", thirty_days_ago) \
        .order("created_at").execute()

    activity = _aggregate_by_day(events.data or [])

    # Quiz performance over time
    quiz_data = db.table("quizzes") \
        .select("score_percentage, completed_at") \
        .eq("project_id", project_id).eq("status", "completed") \
        .order("completed_at").execute()

    quiz_perf = [{"date": q["completed_at"][:10], "score": q["score_percentage"]}
                 for q in (quiz_data.data or [])]

    return {
        "stats": stats,
        "activity_over_time": activity,
        "quiz_performance": quiz_perf,
        "mastery_trends": [],
        "heatmap_data": _build_heatmap(events.data or []),
    }


async def get_global_analytics(user_id: str) -> dict:
    """Get analytics across all user's projects."""
    db = get_supabase()

    spaces = db.table("spaces").select("id", count="exact").eq("user_id", user_id).execute()
    projects = db.table("projects").select("id", count="exact").eq("user_id", user_id).execute()
    quizzes = db.table("quizzes").select("id, score_percentage", count="exact") \
        .eq("user_id", user_id).eq("status", "completed").execute()
    mastery = db.table("concept_mastery").select("mastery_score") \
        .eq("user_id", user_id).execute()

    scores = [m["mastery_score"] for m in (mastery.data or [])]
    avg_mastery = round(sum(scores) / len(scores), 1) if scores else 0
    quiz_scores = [q["score_percentage"] for q in (quizzes.data or []) if q.get("score_percentage")]
    avg_quiz = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0

    # Activity heatmap (last 90 days)
    ninety_days_ago = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    events = db.table("learning_events").select("event_type, created_at") \
        .eq("user_id", user_id).gte("created_at", ninety_days_ago) \
        .order("created_at").execute()

    stats = [
        {"label": "Spaces", "value": spaces.count or 0},
        {"label": "Projects", "value": projects.count or 0},
        {"label": "Quizzes", "value": quizzes.count or 0},
        {"label": "Avg Quiz Score", "value": f"{avg_quiz}%"},
        {"label": "Avg Mastery", "value": f"{avg_mastery}%"},
        {"label": "Concepts Learned", "value": len(scores)},
    ]

    return {
        "stats": stats,
        "activity_over_time": _aggregate_by_day(events.data or []),
        "heatmap_data": _build_heatmap(events.data or []),
        "quiz_performance": [],
        "mastery_trends": [],
    }


def _aggregate_by_day(events: list[dict]) -> list[dict]:
    """Group events by day."""
    days: dict[str, int] = {}
    for e in events:
        day = e["created_at"][:10]
        days[day] = days.get(day, 0) + 1
    return [{"date": d, "count": c} for d, c in sorted(days.items())]


def _build_heatmap(events: list[dict]) -> list[dict]:
    """Build GitHub-style contribution heatmap data."""
    days: dict[str, int] = {}
    for e in events:
        day = e["created_at"][:10]
        days[day] = days.get(day, 0) + 1

    return [{"date": d, "count": c, "level": min(4, c)} for d, c in sorted(days.items())]
