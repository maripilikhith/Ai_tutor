"""
AI Study Companion — Recommendation Prompt Template

Generates personalized learning recommendations based on
mastery data, quiz history, growth trends, and repeated mistakes.
"""


def build_recommendation_prompt(
    learning_goal: str,
    mastery_summary: str,
    recent_quiz_results: str,
    growth_trends: str,
    repeated_mistakes: str,
    previous_recommendations: str,
    available_materials: str,
) -> str:
    """Build prompt for generating learning recommendations."""
    return f"""Based on the learner's current state, generate personalized learning
recommendations.

LEARNING GOAL: {learning_goal}

CURRENT MASTERY:
{mastery_summary}

RECENT QUIZ RESULTS:
{recent_quiz_results}

GROWTH TRENDS:
{growth_trends}

REPEATED MISTAKES:
{repeated_mistakes}

PREVIOUS RECOMMENDATIONS (avoid repeating):
{previous_recommendations}

AVAILABLE MATERIALS:
{available_materials}

Generate 2-3 actionable recommendations. Return as JSON:
{{
  "recommendations": [
    {{
      "type": "revisit_concept | take_quiz | review_material | practice_weakness | advance_topic",
      "title": "Short action title",
      "description": "Detailed, specific recommendation with references to
        materials and page numbers where applicable",
      "priority": "high | medium | low",
      "related_concepts": ["concept names"],
      "related_materials": ["material names"]
    }}
  ]
}}

Prioritize: weaknesses > declining trends > untested concepts > advancing strong areas

RULES:
- Be specific — reference actual materials and concepts
- Don't repeat previous recommendations
- Each recommendation should have a clear, achievable action
- High priority for declining or repeatedly-failed concepts"""
