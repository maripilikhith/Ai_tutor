"""Analytics Feature — Schemas"""
from pydantic import BaseModel

class StatCard(BaseModel):
    label: str
    value: float | int | str
    change: float | None = None
    trend: str = ""  # up, down, neutral

class AnalyticsResponse(BaseModel):
    stats: list[StatCard] = []
    activity_over_time: list[dict] = []
    mastery_trends: list[dict] = []
    quiz_performance: list[dict] = []
    heatmap_data: list[dict] = []
