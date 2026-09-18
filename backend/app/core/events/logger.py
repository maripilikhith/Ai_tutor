"""
AI Study Companion — Learning Event Logger

Logs all learning activities to the learning_events table.
These events power:
- Activity timelines on dashboards
- Analytics (project, global, admin)
- Admin activity logs

Every user action that represents learning progress is captured here.
"""

import uuid
from app.core.database.supabase import get_supabase


async def log_event(
    user_id: str,
    event_type: str,
    event_data: dict | None = None,
    project_id: str | None = None,
    space_id: str | None = None,
) -> None:
    """
    Log a learning event.

    Args:
        user_id: The user who performed the action
        event_type: One of the defined event types (see below)
        event_data: Flexible JSON payload with event-specific data
        project_id: Associated project (if applicable)
        space_id: Associated space (if applicable)

    Event Types:
        - space_created
        - project_created
        - material_uploaded
        - material_processed
        - material_failed
        - tutor_message_sent
        - tutor_response_received
        - quiz_started
        - quiz_question_answered
        - quiz_completed
        - mastery_updated
        - recommendation_generated
        - recommendation_completed
        - recommendation_dismissed
        - learner_context_updated
        - repeated_mistake_detected
    """
    try:
        db = get_supabase()
        idempotency_key = f"{event_type}:{user_id}:{uuid.uuid4().hex[:8]}"

        db.table("learning_events").insert({
            "user_id": user_id,
            "project_id": project_id,
            "space_id": space_id,
            "event_type": event_type,
            "event_data": event_data or {},
            "idempotency_key": idempotency_key,
        }).execute()
    except Exception:
        # Event logging should never crash the application
        pass
