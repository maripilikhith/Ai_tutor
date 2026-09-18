"""
Quiz Feature — Question Generator

Generates MCQ and open-ended questions using Gemini with structured output.
"""

from app.core.ai.gemini import generate_structured
from app.core.ai.rag import retrieve_context, format_context_for_prompt
from app.core.ai.prompts.quiz import build_mcq_prompt, build_open_ended_prompt
from app.features.quiz.schemas import MCQQuestion, OpenEndedQuestion


async def generate_mcq(
    concept_name: str,
    concept_description: str,
    project_id: str,
    user_id: str,
    difficulty: str = "medium",
    mastery_score: float = 50.0,
    previous_questions: list[str] = None,
) -> MCQQuestion:
    """
    Generate a multiple-choice question for a concept.

    Uses RAG to ground the question in actual learning materials.
    Falls back to concept name/description only if RAG is unavailable.

    Returns:
        MCQQuestion with question_text, options, correct_answer, explanation
    """
    # Try to get relevant chunks — gracefully degrade if embedding API is down
    context = "No additional context available."
    try:
        chunks = await retrieve_context(
            query=f"{concept_name}: {concept_description}",
            project_id=project_id,
            user_id=user_id,
            top_k=3,
        )
        context = format_context_for_prompt(chunks)
    except Exception as e:
        print(f"[Quiz] RAG retrieval failed for MCQ ({concept_name}), using concept only: {e}")

    prompt = build_mcq_prompt(
        concept_name=concept_name,
        concept_description=concept_description,
        knowledge_chunks=context,
        difficulty=difficulty,
        mastery_score=mastery_score,
        previous_questions=previous_questions,
    )

    result = await generate_structured(
        prompt=prompt,
        response_schema=MCQQuestion,
        system_prompt="You are a quiz question generator. Generate high-quality assessment questions.",
        temperature=0.5,
        user_id=user_id,
        project_id=project_id,
        feature="quiz_generation",
    )

    return result


async def generate_open_ended(
    concept_name: str,
    concept_description: str,
    project_id: str,
    user_id: str,
    difficulty: str = "medium",
    previous_questions: list[str] = None,
) -> OpenEndedQuestion:
    """
    Generate an open-ended question for a concept.

    Returns:
        OpenEndedQuestion with question_text, expected_key_points, rubric
    """
    # Try to get relevant chunks — gracefully degrade if embedding API is down
    context = "No additional context available."
    try:
        chunks = await retrieve_context(
            query=f"{concept_name}: {concept_description}",
            project_id=project_id,
            user_id=user_id,
            top_k=3,
        )
        context = format_context_for_prompt(chunks)
    except Exception as e:
        print(f"[Quiz] RAG retrieval failed for open-ended ({concept_name}), using concept only: {e}")

    prompt = build_open_ended_prompt(
        concept_name=concept_name,
        concept_description=concept_description,
        knowledge_chunks=context,
        difficulty=difficulty,
        previous_questions=previous_questions,
    )

    result = await generate_structured(
        prompt=prompt,
        response_schema=OpenEndedQuestion,
        system_prompt="You are a quiz question generator. Generate thoughtful assessment questions.",
        temperature=0.5,
        user_id=user_id,
        project_id=project_id,
        feature="quiz_generation",
    )

    return result
