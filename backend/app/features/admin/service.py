"""
Admin Feature — Business Logic

Admin dashboard: user management, system health, AI usage, activity logs.
"""

from app.core.database.supabase import get_supabase
from app.core.cache.redis import get_redis
from app.core.exceptions import NotFoundError


async def get_admin_dashboard() -> dict:
    """Get admin dashboard overview."""
    db = get_supabase()

    users = db.table("profiles").select("id", count="exact").execute()
    spaces = db.table("spaces").select("id", count="exact").execute()
    projects = db.table("projects").select("id", count="exact").execute()
    quizzes = db.table("quizzes").select("id", count="exact") \
        .eq("status", "completed").execute()
    pending_jobs = db.table("background_jobs").select("id", count="exact") \
        .eq("status", "queued").execute()
    failed_jobs = db.table("background_jobs").select("id", count="exact") \
        .eq("status", "failed").execute()

    return {
        "total_users": users.count or 0,
        "total_spaces": spaces.count or 0,
        "total_projects": projects.count or 0,
        "total_quizzes": quizzes.count or 0,
        "pending_jobs": pending_jobs.count or 0,
        "failed_jobs": failed_jobs.count or 0,
    }


async def list_users(page: int = 1, page_size: int = 20) -> dict:
    """List all users with stats."""
    db = get_supabase()

    start = (page - 1) * page_size
    end = start + page_size - 1

    result = db.table("profiles") \
        .select("*") \
        .order("created_at", desc=True) \
        .range(start, end) \
        .execute()

    total = db.table("profiles").select("id", count="exact").execute()

    users = []
    for profile in (result.data or []):
        space_count = db.table("spaces").select("id", count="exact") \
            .eq("user_id", profile["id"]).execute()
        project_count = db.table("projects").select("id", count="exact") \
            .eq("user_id", profile["id"]).execute()
        quiz_count = db.table("quizzes").select("id", count="exact") \
            .eq("user_id", profile["id"]).eq("status", "completed").execute()

        users.append({
            **profile,
            "space_count": space_count.count or 0,
            "project_count": project_count.count or 0,
            "quiz_count": quiz_count.count or 0,
        })

    return {"items": users, "total": total.count or 0, "page": page, "page_size": page_size}


async def get_user_detail(user_id: str) -> dict:
    """Get detailed info about a user for admin inspection."""
    db = get_supabase()

    profile = db.table("profiles").select("*") \
        .eq("id", user_id).single().execute()
    if not profile.data:
        raise NotFoundError("User", user_id)

    spaces = db.table("spaces").select("id, name, created_at") \
        .eq("user_id", user_id).execute()
    projects = db.table("projects").select("id, name, space_id, created_at") \
        .eq("user_id", user_id).execute()
    recent_events = db.table("learning_events").select("*") \
        .eq("user_id", user_id).order("created_at", desc=True).limit(20).execute()
    quizzes = db.table("quizzes").select("*") \
        .eq("user_id", user_id).eq("status", "completed") \
        .order("completed_at", desc=True).limit(10).execute()

    ai_logs = db.table("ai_usage_logs").select("feature, total_tokens, estimated_cost_usd") \
        .eq("user_id", user_id).execute()
    
    ai_data = ai_logs.data or []
    total_tokens = sum(l.get("total_tokens", 0) for l in ai_data)
    total_cost = sum(l.get("estimated_cost_usd", 0) for l in ai_data)
    
    by_feature = {}
    for l in ai_data:
        feat = l.get("feature", "other")
        if feat not in by_feature:
            by_feature[feat] = {"requests": 0, "tokens": 0}
        by_feature[feat]["requests"] += 1
        by_feature[feat]["tokens"] += l.get("total_tokens", 0)
        
    by_feature_list = [{"feature": f, "requests": d["requests"], "tokens": d["tokens"]} for f, d in by_feature.items()]

    ai_usage = {
        "total_requests": len(ai_data),
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "by_feature": by_feature_list
    }

    return {
        "profile": profile.data,
        "spaces": spaces.data or [],
        "projects": projects.data or [],
        "recent_activity": recent_events.data or [],
        "recent_quizzes": quizzes.data or [],
        "ai_usage": ai_usage,
    }


async def get_ai_usage_stats() -> dict:
    """Get AI usage metrics for admin dashboard."""
    db = get_supabase()

    logs = db.table("ai_usage_logs").select("*") \
        .order("created_at", desc=True).execute()

    data = logs.data or []
    total_requests = len(data)
    total_tokens = sum(l.get("total_tokens", 0) for l in data)
    total_cost = sum(l.get("estimated_cost_usd", 0) for l in data)
    errors = sum(1 for l in data if l.get("status") == "error")
    avg_latency = sum(l.get("latency_ms", 0) for l in data) / max(1, total_requests)

    feature_stats = {}
    for l in data:
        feat = l.get("feature", "other")
        if feat not in feature_stats:
            feature_stats[feat] = {"requests": 0, "tokens": 0}
        feature_stats[feat]["requests"] += 1
        feature_stats[feat]["tokens"] += l.get("total_tokens", 0)

    by_feature_list = [{"feature": f, "requests": d["requests"], "tokens": d["tokens"]} for f, d in feature_stats.items()]
    success_rate = 1.0 - (errors / max(1, total_requests))

    return {
        "total_requests": total_requests,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "error_count": errors,
        "error_rate": round(errors / max(1, total_requests) * 100, 1),
        "success_rate": success_rate,
        "avg_latency_ms": round(avg_latency),
        "by_feature": by_feature_list,
        "recent_logs": data[:20],
    }


async def get_activity_log(page: int = 1, page_size: int = 50) -> dict:
    """Get global activity log for admin."""
    db = get_supabase()
    start = (page - 1) * page_size
    end = start + page_size - 1

    result = db.table("learning_events").select("*") \
        .order("created_at", desc=True).range(start, end).execute()
    total = db.table("learning_events").select("id", count="exact").execute()

    return {"items": result.data or [], "total": total.count or 0}


async def get_system_health() -> dict:
    """Check system component health."""
    health = {"status": "healthy", "database": "connected", "ai_service": "unknown", "cache": "unknown"}

    # Check DB
    try:
        db = get_supabase()
        db.table("profiles").select("id").limit(1).execute()
        health["database"] = "connected"
    except Exception:
        health["database"] = "error"
        health["status"] = "degraded"

    # Check Redis
    try:
        client = get_redis()
        if client:
            client.ping()
            health["cache"] = "connected"
        else:
            health["cache"] = "not_configured"
    except Exception:
        health["cache"] = "error"

    # Check pending jobs
    try:
        pending = db.table("background_jobs").select("id", count="exact") \
            .eq("status", "queued").execute()
        failed = db.table("background_jobs").select("id", count="exact") \
            .eq("status", "failed").execute()
        health["pending_jobs"] = pending.count or 0
        health["failed_jobs"] = failed.count or 0
    except Exception:
        pass

    return health
