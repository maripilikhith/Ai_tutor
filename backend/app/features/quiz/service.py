"""
Quiz Feature — Business Logic

Orchestrates the adaptive quiz flow:
1. Start quiz — select concepts based on priority algorithm
2. Generate questions — alternate MCQ and open-ended
3. Submit answer — evaluate and update quiz state
4. Complete quiz — calculate score and trigger post-quiz workflow
"""

import json
import random
from app.core.database.supabase import get_supabase
from app.core.events.logger import log_event
from app.core.exceptions import NotFoundError, BadRequestError
from app.features.quiz.generator import generate_mcq, generate_open_ended
from app.features.quiz.evaluator import evaluate_mcq, evaluate_open_ended


async def start_quiz(
    project_id: str,
    user_id: str,
    total_questions: int = 10,
) -> dict:
    """
    Start a new quiz.

    Steps:
    1. Select concepts using the priority algorithm
    2. Create quiz record
    3. Generate the first question
    4. Return the first question to the user
    """
    db = get_supabase()

    # Get all concepts for this project
    concepts = db.table("concepts") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    if not concepts.data or len(concepts.data) == 0:
        raise BadRequestError(
            "No concepts available. Upload and process materials first."
        )

    # Get current mastery for priority scoring
    mastery_data = db.table("concept_mastery") \
        .select("concept_id, mastery_score, trend, quiz_attempts, last_tested_at") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .execute()

    mastery_map = {m["concept_id"]: m for m in (mastery_data.data or [])}

    # Score and sort concepts by priority
    scored_concepts = _score_concepts(concepts.data, mastery_map)

    # Create quiz record
    quiz_result = db.table("quizzes") \
        .insert({
            "user_id": user_id,
            "project_id": project_id,
            "total_questions": total_questions,
        }) \
        .execute()

    quiz = quiz_result.data[0]

    # Get previous questions for this concept to avoid repetition
    first_concept = scored_concepts[0]
    recent_questions = db.table("quiz_questions") \
        .select("question_text") \
        .eq("user_id", user_id) \
        .eq("concept_id", first_concept["id"]) \
        .order("created_at", desc=True) \
        .limit(5) \
        .execute()
    previous_questions = [q["question_text"] for q in (recent_questions.data or [])]

    first_question = await _generate_question(
        concept=first_concept,
        mastery_map=mastery_map,
        project_id=project_id,
        user_id=user_id,
        quiz_id=quiz["id"],
        question_order=1,
        total_questions=total_questions,
        prefer_mcq=True,  # Start with MCQ
        previous_questions=previous_questions,
    )

    await log_event(
        user_id=user_id,
        event_type="quiz_started",
        event_data={"quiz_id": quiz["id"], "total_questions": total_questions},
        project_id=project_id,
    )

    return {
        "quiz_id": quiz["id"],
        "total_questions": total_questions,
        "first_question": first_question,
    }


async def submit_answer(
    quiz_id: str,
    question_id: str,
    user_id: str,
    answer: str,
    confidence: int = 50,
) -> dict:
    """
    Submit an answer and get evaluation + next question.

    Steps:
    1. Validate the quiz and question
    2. Evaluate the answer (MCQ or open-ended)
    3. Update the question record
    4. Update quiz counters
    5. Generate and return the next question (if any)
    """
    db = get_supabase()

    # Get the quiz
    quiz = db.table("quizzes") \
        .select("*") \
        .eq("id", quiz_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not quiz.data:
        raise NotFoundError("Quiz", quiz_id)

    if quiz.data["status"] != "in_progress":
        raise BadRequestError("This quiz is already completed.")

    # Get the question
    question = db.table("quiz_questions") \
        .select("*") \
        .eq("id", question_id) \
        .eq("quiz_id", quiz_id) \
        .single() \
        .execute()

    if not question.data:
        raise NotFoundError("Question", question_id)

    if question.data.get("user_answer"):
        raise BadRequestError("This question has already been answered.")

    q = question.data

    # Evaluate the answer
    if q["question_type"] == "mcq":
        q_data = q.get("question_data", {})
        result = await evaluate_mcq(
            user_answer=answer,
            correct_answer=q_data.get("correct_answer", ""),
            explanation=q_data.get("explanation", ""),
        )
    else:  # open_ended
        q_data = q.get("question_data", {})
        result = await evaluate_open_ended(
            question_text=q["question_text"],
            expected_key_points=q_data.get("expected_key_points", []),
            user_answer=answer,
            project_id=quiz.data["project_id"],
            user_id=user_id,
        )

    # Update the question record
    db.table("quiz_questions") \
        .update({
            "user_answer": answer,
            "is_correct": result["is_correct"],
            "score": result["score"],
            "ai_evaluation": result.get("evaluation"),
            "answered_at": "now()",
        }) \
        .eq("id", question_id) \
        .execute()

    # Update quiz counters
    new_answered = quiz.data["answered_count"] + 1
    new_correct = quiz.data["correct_count"] + (1 if result["is_correct"] else 0)

    db.table("quizzes") \
        .update({
            "answered_count": new_answered,
            "correct_count": new_correct,
        }) \
        .eq("id", quiz_id) \
        .execute()

    await log_event(
        user_id=user_id,
        event_type="quiz_question_answered",
        event_data={
            "quiz_id": quiz_id,
            "question_type": q["question_type"],
            "is_correct": result["is_correct"],
            "score": result["score"],
        },
        project_id=quiz.data["project_id"],
    )

    # Generate next question if quiz isn't done
    next_question = None
    if new_answered < quiz.data["total_questions"]:
        # Get concepts and mastery for next question selection
        concepts = db.table("concepts") \
            .select("*") \
            .eq("project_id", quiz.data["project_id"]) \
            .eq("user_id", user_id) \
            .execute()

        mastery_data = db.table("concept_mastery") \
            .select("concept_id, mastery_score, trend, quiz_attempts") \
            .eq("project_id", quiz.data["project_id"]) \
            .eq("user_id", user_id) \
            .execute()

        mastery_map = {m["concept_id"]: m for m in (mastery_data.data or [])}
        scored = _score_concepts(concepts.data or [], mastery_map)

        # Alternate between MCQ and open-ended
        prefer_mcq = (new_answered % 2 == 0)

        next_concept = scored[new_answered % len(scored)]
        recent_questions = db.table("quiz_questions") \
            .select("question_text") \
            .eq("user_id", user_id) \
            .eq("concept_id", next_concept["id"]) \
            .order("created_at", desc=True) \
            .limit(5) \
            .execute()
        previous_questions = [q["question_text"] for q in (recent_questions.data or [])]

        next_question = await _generate_question(
            concept=next_concept,
            mastery_map=mastery_map,
            project_id=quiz.data["project_id"],
            user_id=user_id,
            quiz_id=quiz_id,
            question_order=new_answered + 1,
            total_questions=quiz.data["total_questions"],
            prefer_mcq=prefer_mcq,
            previous_questions=previous_questions,
        )

    response = {
        "is_correct": result["is_correct"],
        "score": result["score"],
        "correct_answer": result.get("correct_answer"),
        "explanation": result.get("explanation", ""),
        "evaluation": result.get("evaluation"),
        "source_reference": q.get("source_reference", ""),
        "next_question": next_question,
    }

    return response


async def complete_quiz(quiz_id: str, user_id: str) -> dict:
    """
    Complete a quiz and calculate final score.
    Triggers the post-quiz workflow (mastery update, recommendations).
    """
    db = get_supabase()

    quiz = db.table("quizzes") \
        .select("*") \
        .eq("id", quiz_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not quiz.data:
        raise NotFoundError("Quiz", quiz_id)

    # Calculate final score
    total = quiz.data["answered_count"] or 1
    correct = quiz.data["correct_count"]
    score_pct = round((correct / total) * 100, 1)

    # Update quiz
    db.table("quizzes") \
        .update({
            "status": "completed",
            "score_percentage": score_pct,
            "completed_at": "now()",
        }) \
        .eq("id", quiz_id) \
        .execute()

    # Get concepts tested
    questions = db.table("quiz_questions") \
        .select("concept_id, is_correct, score, question_type, concepts(name)") \
        .eq("quiz_id", quiz_id) \
        .execute()

    concepts_tested = []
    for q in (questions.data or []):
        name = q.get("concepts", {}).get("name", "Unknown") if q.get("concepts") else "Unknown"
        concepts_tested.append({
            "concept_name": name,
            "is_correct": q.get("is_correct", False),
            "score": q.get("score", 0),
        })

    # Create background job for post-quiz workflow
    db.table("background_jobs").insert({
        "user_id": user_id,
        "job_type": "post_quiz_workflow",
        "payload": {
            "quiz_id": quiz_id,
            "project_id": quiz.data["project_id"],
        },
        "priority": 2,
    }).execute()

    await log_event(
        user_id=user_id,
        event_type="quiz_completed",
        event_data={
            "quiz_id": quiz_id,
            "score_percentage": score_pct,
            "correct_count": correct,
            "total_questions": total,
        },
        project_id=quiz.data["project_id"],
    )

    return {
        "quiz_id": quiz_id,
        "total_questions": total,
        "correct_count": correct,
        "score_percentage": score_pct,
        "concepts_tested": concepts_tested,
        "completed_at": quiz.data.get("completed_at"),
    }


async def list_quizzes(project_id: str, user_id: str) -> dict:
    """List all quizzes for a project."""
    db = get_supabase()

    result = db.table("quizzes") \
        .select("*") \
        .eq("project_id", project_id) \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()

    return {"items": result.data or [], "total": len(result.data or [])}


# ── Private Helpers ──

def _score_concepts(concepts: list[dict], mastery_map: dict) -> list[dict]:
    """
    Score and sort concepts by quiz priority.

    Priority algorithm (from blueprint §15):
    - Low mastery → higher priority
    - Declining trend → higher priority
    - Never tested → higher priority
    - Repeated mistakes → highest priority
    """
    scored = []
    for concept in concepts:
        mastery = mastery_map.get(concept["id"])
        score = 50  # Base priority score

        if mastery:
            m_score = mastery["mastery_score"]
            trend = mastery["trend"]
            attempts = mastery["quiz_attempts"]

            # Lower mastery = higher priority
            score += (100 - m_score) * 0.5

            # Declining trend bonus
            if trend == "declining":
                score += 30
            elif trend == "new":
                score += 20

            # Few attempts bonus
            if attempts < 3:
                score += 15
        else:
            # Never tested — high priority
            score += 40

        concept["_priority"] = score
        scored.append(concept)

    # Sort by priority (highest first), with randomization for variety
    scored.sort(key=lambda c: c["_priority"], reverse=True)

    # Add slight randomization to avoid always testing the same concept
    if len(scored) > 3:
        top_group = scored[:5]
        random.shuffle(top_group)
        scored[:5] = top_group

    return scored


async def _generate_question(
    concept: dict,
    mastery_map: dict,
    project_id: str,
    user_id: str,
    quiz_id: str,
    question_order: int,
    total_questions: int,
    prefer_mcq: bool = True,
    previous_questions: list[str] = None,
) -> dict:
    """Generate and store a quiz question for a concept."""
    db = get_supabase()

    mastery = mastery_map.get(concept["id"])
    mastery_score = mastery["mastery_score"] if mastery else 50.0

    # Determine difficulty from mastery
    if mastery_score >= 75:
        difficulty = "hard"
    elif mastery_score >= 40:
        difficulty = "medium"
    else:
        difficulty = "easy"

    question_type = "mcq" if prefer_mcq else "open_ended"

    try:
        if question_type == "mcq":
            q = await generate_mcq(
                concept_name=concept["name"],
                concept_description=concept.get("description", ""),
                project_id=project_id,
                user_id=user_id,
                difficulty=difficulty,
                mastery_score=mastery_score,
                previous_questions=previous_questions,
            )
            question_data = q.model_dump()
            question_text = q.question_text
        else:
            q = await generate_open_ended(
                concept_name=concept["name"],
                concept_description=concept.get("description", ""),
                project_id=project_id,
                user_id=user_id,
                difficulty=difficulty,
                previous_questions=previous_questions,
            )
            question_data = q.model_dump()
            question_text = q.question_text
    except Exception:
        # Fallback to MCQ if open-ended generation fails
        question_type = "mcq"
        q = await generate_mcq(
            concept_name=concept["name"],
            concept_description=concept.get("description", ""),
            project_id=project_id,
            user_id=user_id,
            difficulty=difficulty,
            mastery_score=mastery_score,
            previous_questions=previous_questions,
        )
        question_data = q.model_dump()
        question_text = q.question_text

    # Store the question
    result = db.table("quiz_questions").insert({
        "quiz_id": quiz_id,
        "user_id": user_id,
        "concept_id": concept["id"],
        "question_type": question_type,
        "difficulty": difficulty,
        "question_text": question_text,
        "question_data": question_data,
        "question_order": question_order,
        "source_reference": question_data.get("source_reference", ""),
    }).execute()

    question_record = result.data[0]

    # Build response (hide correct answer for MCQ)
    response = {
        "question_id": question_record["id"],
        "question_type": question_type,
        "difficulty": difficulty,
        "question_text": question_text,
        "concept_name": concept["name"],
        "question_order": question_order,
        "total_questions": total_questions,
    }

    if question_type == "mcq":
        # Send options WITHOUT is_correct
        response["options"] = [
            {"label": opt["label"], "text": opt["text"]}
            for opt in question_data.get("options", [])
        ]

    # Include source reference so UI can show which PDF page this came from
    response["source_reference"] = question_data.get("source_reference", "")

    return response

async def delete_quiz(quiz_id: str, user_id: str) -> dict:
    '''Delete a quiz.'''
    db = get_supabase()
    
    # Verify ownership
    quiz = db.table('quizzes').select('id').eq('id', quiz_id).eq('user_id', user_id).execute()
    if not quiz.data:
        raise NotFoundError('Quiz not found')
        
    db.table('quizzes').delete().eq('id', quiz_id).execute()
    
    return {'status': 'success', 'message': 'Quiz deleted'}

