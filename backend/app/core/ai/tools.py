"""
AI Study Companion — AI Function Calling Tool Definitions

Defines the tools that the AI Tutor can call during conversations.
These are registered as function declarations with Gemini's function calling API.
"""

from google.genai import types


# ── Tool Definitions ──
# These are the functions the AI Tutor can request to call

TUTOR_TOOLS = [
    types.Tool(functions=[
        types.FunctionDeclaration(
            name="search_materials",
            description="Search the user's learning materials for specific information. Use this when you need to find information about a topic that isn't in your current context.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "query": types.Schema(
                        type="STRING",
                        description="The search query to find relevant information"
                    ),
                },
                required=["query"],
            ),
        ),
        types.FunctionDeclaration(
            name="get_mastery_summary",
            description="Get the user's current mastery levels for all concepts in this project.",
            parameters=types.Schema(
                type="OBJECT",
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="get_recent_quiz_performance",
            description="Get the user's recent quiz results and performance trends.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "limit": types.Schema(
                        type="INTEGER",
                        description="Number of recent quizzes to retrieve (default 5)"
                    ),
                },
            ),
        ),
        types.FunctionDeclaration(
            name="get_learner_context",
            description="Get the user's learner profile including strengths, weaknesses, and learning preferences.",
            parameters=types.Schema(
                type="OBJECT",
                properties={},
            ),
        ),
        types.FunctionDeclaration(
            name="record_learning_insight",
            description="Record an important learning insight about the user. Use when you notice a pattern in their understanding.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "insight_type": types.Schema(
                        type="STRING",
                        description="Type: strength, weakness, preference, important_insight",
                        enum=["strength", "weakness", "preference", "important_insight"],
                    ),
                    "content": types.Schema(
                        type="STRING",
                        description="The insight content"
                    ),
                },
                required=["insight_type", "content"],
            ),
        ),
    ]),
]
