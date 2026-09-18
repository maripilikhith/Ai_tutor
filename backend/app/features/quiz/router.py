"""
Quiz Feature — API Routes

Start, answer, and complete quiz endpoints.
"""

from fastapi import APIRouter
from app.dependencies import CurrentUser
from app.features.quiz import service, schemas

router = APIRouter()


@router.post("/projects/{project_id}/quiz/start")
async def start_quiz(
    project_id: str,
    data: schemas.QuizStartRequest,
    current_user: CurrentUser,
):
    """Start a new adaptive quiz for a project."""
    return await service.start_quiz(
        project_id=project_id,
        user_id=current_user["user_id"],
        total_questions=data.total_questions,
    )


@router.post("/quiz/{quiz_id}/answer", response_model=schemas.AnswerResponse)
async def submit_answer(
    quiz_id: str,
    data: schemas.AnswerSubmitRequest,
    current_user: CurrentUser,
):
    """Submit an answer to a quiz question."""
    return await service.submit_answer(
        quiz_id=quiz_id,
        question_id=data.question_id,
        user_id=current_user["user_id"],
        answer=data.answer,
        confidence=data.confidence,
    )


@router.post("/quiz/{quiz_id}/complete", response_model=schemas.QuizSummary)
async def complete_quiz(quiz_id: str, current_user: CurrentUser):
    """Complete a quiz and get the summary."""
    return await service.complete_quiz(quiz_id, current_user["user_id"])


@router.get("/projects/{project_id}/quizzes", response_model=schemas.QuizListResponse)
async def list_quizzes(project_id: str, current_user: CurrentUser):
    """List all quizzes for a project."""
    return await service.list_quizzes(project_id, current_user["user_id"])

@router.delete('/quiz/{quiz_id}')
async def delete_quiz(quiz_id: str, current_user: CurrentUser):
    '''Delete a quiz and its history.'''
    return await service.delete_quiz(quiz_id, current_user['user_id'])

