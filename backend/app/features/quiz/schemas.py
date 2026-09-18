"""
Quiz Feature — Pydantic Schemas

Request/response models for the adaptive quiz system.
Also includes AI structured output schemas for question generation and evaluation.
"""

from pydantic import BaseModel, Field
from datetime import datetime


# ── Request Schemas ──

class QuizStartRequest(BaseModel):
    """Start a new quiz."""
    total_questions: int = Field(10, ge=3, le=20)


class AnswerSubmitRequest(BaseModel):
    """Submit an answer to a quiz question."""
    question_id: str
    answer: str
    confidence: int = Field(50, ge=0, le=100)  # Self-reported confidence


# ── AI Structured Output Schemas ──

class MCQOption(BaseModel):
    """A single MCQ option."""
    label: str
    text: str
    is_correct: bool


class MCQQuestion(BaseModel):
    """AI-generated MCQ question."""
    question_text: str
    options: list[MCQOption]
    correct_answer: str
    explanation: str
    source_reference: str


class OpenEndedQuestion(BaseModel):
    """AI-generated open-ended question."""
    question_text: str
    expected_key_points: list[str]
    rubric: str
    source_reference: str


class EvaluationResult(BaseModel):
    """AI evaluation of an open-ended answer."""
    score: int
    understanding: str
    accuracy: str
    relevance: str
    key_concepts_covered: list[str]
    missing_concepts: list[str]
    strengths: list[str]
    weaknesses: list[str]
    feedback: str


# ── Response Schemas ──

class QuestionResponse(BaseModel):
    """A quiz question sent to the frontend."""
    question_id: str
    question_type: str  # mcq or open_ended
    difficulty: str
    question_text: str
    concept_name: str = ""
    options: list[dict] = []  # MCQ options (without is_correct)
    question_order: int
    total_questions: int


class AnswerResponse(BaseModel):
    """Response after submitting an answer."""
    is_correct: bool
    score: float
    correct_answer: str | None = None  # For MCQ
    explanation: str = ""
    evaluation: dict | None = None  # AI evaluation for open-ended
    next_question: QuestionResponse | None = None


class QuizSummary(BaseModel):
    """Quiz completion summary."""
    quiz_id: str
    total_questions: int
    correct_count: int
    score_percentage: float
    concepts_tested: list[dict] = []
    completed_at: datetime | None = None


class QuizRecord(BaseModel):
    """Record of a quiz for listing history."""
    id: str
    total_questions: int
    answered_count: int
    correct_count: int
    score_percentage: float
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class QuizListResponse(BaseModel):
    """List of quizzes."""
    items: list[QuizRecord]
    total: int
