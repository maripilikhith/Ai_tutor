"""
Mastery Feature — Schemas
"""

from pydantic import BaseModel
from datetime import datetime


class ConceptMasteryResponse(BaseModel):
    id: str
    concept_id: str
    concept_name: str = ""
    mastery_score: float
    trend: str
    quiz_attempts: int
    correct_count: int
    incorrect_count: int
    last_tested_at: datetime | None = None


class MasteryListResponse(BaseModel):
    items: list[ConceptMasteryResponse]
    total: int
    avg_mastery: float = 0.0


class GrowthDataPoint(BaseModel):
    date: str
    concept_name: str
    mastery_score: float


class GrowthResponse(BaseModel):
    data_points: list[GrowthDataPoint]
    concepts: list[str]
