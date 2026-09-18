"""Home Feature — Dashboard API"""
from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.core.database.supabase import get_supabase

router = APIRouter()

@router.get("/api/home")
async def get_home_dashboard(current_user: CurrentUser):
    """
    Home dashboard data — recent activity, space overview, stats.
    """
    user_id = current_user["user_id"]
    db = get_supabase()

    # Profile
    profile = db.table("profiles").select("*") \
        .eq("id", user_id).single().execute()

    # Spaces with project counts
    spaces = db.table("spaces").select("*") \
        .eq("user_id", user_id).order("updated_at", desc=True).execute()

    for space in (spaces.data or []):
        pc = db.table("projects").select("id", count="exact") \
            .eq("space_id", space["id"]).execute()
        space["project_count"] = pc.count or 0

    # Recent activity (last 10 events)
    activity = db.table("learning_events").select("*") \
        .eq("user_id", user_id).order("created_at", desc=True).limit(10).execute()

    # Active recommendations across all projects
    recs = db.table("recommendations").select("*") \
        .eq("user_id", user_id).eq("status", "active") \
        .order("created_at", desc=True).limit(5).execute()

    # Overall stats
    total_projects = db.table("projects").select("id", count="exact") \
        .eq("user_id", user_id).execute()
    total_quizzes = db.table("quizzes").select("id", count="exact") \
        .eq("user_id", user_id).eq("status", "completed").execute()
    mastery_data = db.table("concept_mastery").select("mastery_score") \
        .eq("user_id", user_id).execute()

    scores = [m["mastery_score"] for m in (mastery_data.data or [])]
    avg_mastery = round(sum(scores) / len(scores), 1) if scores else 0

    return {
        "profile": profile.data,
        "spaces": spaces.data or [],
        "recent_activity": activity.data or [],
        "recommendations": recs.data or [],
        "stats": {
            "total_spaces": len(spaces.data or []),
            "total_projects": total_projects.count or 0,
            "total_quizzes": total_quizzes.count or 0,
            "avg_mastery": avg_mastery,
            "concepts_learned": len(scores),
        },
    }
