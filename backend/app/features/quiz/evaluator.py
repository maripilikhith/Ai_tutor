"""
Quiz Feature — Answer Evaluator

Evaluates quiz answers:
- MCQ: Direct comparison (instant)
- Open-ended: AI evaluation with structured feedback (Gemini)
"""

from app.core.ai.gemini import generate_structured
from app.core.ai.rag import retrieve_context, format_context_for_prompt
from app.core.ai.prompts.evaluation import build_evaluation_prompt
from app.features.quiz.schemas import EvaluationResult


async def evaluate_mcq(
    user_answer: str,
    correct_answer: str,
    explanation: str,
) -> dict:
    """
    Evaluate an MCQ answer. Simple string comparison.

    Returns:
        {
            "is_correct": bool,
            "score": 100 or 0,
            "correct_answer": str,
            "explanation": str,
        }
    """
    is_correct = user_answer.strip().upper() == correct_answer.strip().upper()

    return {
        "is_correct": is_correct,
        "score": 100.0 if is_correct else 0.0,
        "correct_answer": correct_answer,
        "explanation": explanation,
    }


async def evaluate_open_ended(
    question_text: str,
    expected_key_points: list[str],
    user_answer: str,
    project_id: str,
    user_id: str,
) -> dict:
    """
    Evaluate an open-ended answer using AI.

    Returns structured evaluation with:
    - score (0-100)
    - understanding, accuracy, relevance assessments
    - covered/missing concepts
    - strengths/weaknesses
    - constructive feedback
    """
    # Get relevant chunks for context
    chunks = await retrieve_context(
        query=question_text,
        project_id=project_id,
        user_id=user_id,
        top_k=3,
    )
    context = format_context_for_prompt(chunks)

    prompt = build_evaluation_prompt(
        question_text=question_text,
        expected_key_points=expected_key_points,
        user_answer=user_answer,
        knowledge_chunks=context,
    )

    evaluation = await generate_structured(
        prompt=prompt,
        response_schema=EvaluationResult,
        system_prompt="You are a fair and constructive educational evaluator.",
        temperature=0.3,  # Low temperature for consistent evaluation
        user_id=user_id,
        project_id=project_id,
        feature="quiz_evaluation",
    )

    is_correct = evaluation.score >= 60  # 60% threshold for "correct"

    return {
        "is_correct": is_correct,
        "score": float(evaluation.score),
        "evaluation": evaluation.model_dump(),
    }
