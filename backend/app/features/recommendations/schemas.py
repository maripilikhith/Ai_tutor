"""Recommendations Feature — Schemas"""
from pydantic import BaseModel
from datetime import datetime

class RecommendationResponse(BaseModel):
    id: str
    type: str
    title: str
    description: str
    priority: str
    related_concepts: list[str] = []
    related_materials: list[str] = []
    status: str
    created_at: datetime

class RecommendationListResponse(BaseModel):
    items: list[RecommendationResponse]
    total: int
