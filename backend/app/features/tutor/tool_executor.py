"""
Tutor Feature — Tool Executor

Handles AI function calls (tools) during Tutor conversations.
When Gemini requests to call a function, this module executes it
and returns the result back to the AI.
"""

from app.core.database.supabase import get_supabase
from app.core.ai.rag import retrieve_context, format_context_for_prompt


async def execute_tool(
    tool_name: str,
    tool_args: dict,
    project_id: str,
    user_id: str,
) -> str:
    """
    Execute a tool requested by the AI Tutor.

    Args:
        tool_name: Name of the tool to execute
        tool_args: Arguments provided by the AI
        project_id: Current project context
        user_id: Current user

    Returns:
        String result to feed back to the AI
    """
    executors = {
        "search_materials": _search_materials,
        "get_mastery_summary": _get_mastery_summary,
        "get_recent_quiz_performance": _get_recent_quiz_performance,
        "get_learner_context": _get_learner_context,
        "record_learning_insight": _record_learning_insight,
    }

    executor = executors.get(tool_name)
    if not executor:
        return f"Unknown tool: {tool_name}"

    return await executor(tool_args, project_id, user_id)


async def _search_materials(args: dict, project_id: str, user_id: str) -> str:
    """Search the user's learning materials."""
    query = args.get("query", "")
    if not query:
        return "No search query provided."

    chunks = await retrieve_context(
        query=query,
        project_id=project_id,
        user_id=user_id,
        top_k=3,
    )

    if not chunks:
        return "No relevant information found in the learning materials."

    return format_context_for_prompt(chunks)


async def _get_mastery_summary(args: dict, project_id: str, user_id: str) -> str:
    """Get current mastery levels for all concepts."""
    db = get_supabase()

    result = db.table("concept_mastery") \
        .select("mastery_score, trend, quiz_attempts, concepts(name)") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("mastery_score") \
        .execute()

    if not result.data:
        return "No mastery data available yet. The user hasn't taken any quizzes."

    lines = ["Concept Mastery Levels:"]
    for m in result.data:
        name = m.get("concepts", {}).get("name", "Unknown") if m.get("concepts") else "Unknown"
        score = m["mastery_score"]
        trend = m["trend"]
        attempts = m["quiz_attempts"]
        lines.append(f"  - {name}: {score:.0f}% ({trend}, {attempts} attempts)")

    return "\n".join(lines)


async def _get_recent_quiz_performance(args: dict, project_id: str, user_id: str) -> str:
    """Get recent quiz results."""
    db = get_supabase()
    limit = args.get("limit", 5)

    result = db.table("quizzes") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .eq("status", "completed") \
        .order("completed_at", desc=True) \
        .limit(limit) \
        .execute()

    if not result.data:
        return "No quizzes completed yet."

    lines = ["Recent Quiz Results:"]
    for q in result.data:
        lines.append(
            f"  - Score: {q['score_percentage']:.0f}% "
            f"({q['correct_count']}/{q['total_questions']} correct) "
            f"on {q['completed_at'][:10]}"
        )

    return "\n".join(lines)


async def _get_learner_context(args: dict, project_id: str, user_id: str) -> str:
    """Get the learner's profile."""
    db = get_supabase()

    result = db.table("learner_context") \
        .select("context_type, content") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .eq("is_active", True) \
        .execute()

    if not result.data:
        return "No learner context available yet."

    lines = ["Learner Profile:"]
    for item in result.data:
        lines.append(f"  [{item['context_type']}] {item['content']}")

    return "\n".join(lines)


async def _record_learning_insight(args: dict, project_id: str, user_id: str) -> str:
    """Record a learning insight about the user."""
    db = get_supabase()

    insight_type = args.get("insight_type", "important_insight")
    content = args.get("content", "")

    if not content:
        return "No insight content provided."

    db.table("learner_context").insert({
        "user_id": user_id,
        "project_id": project_id,
        "context_type": insight_type,
        "content": content,
        "source": "tutor",
    }).execute()

    return f"Recorded {insight_type}: {content}"
