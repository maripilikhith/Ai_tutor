"""Profile Feature — Schemas"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ProfileResponse(BaseModel):
    id: str
    full_name: str = ""
    email: str = ""
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    use_custom_key: bool = False
    gemini_api_key: Optional[str] = None


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    use_custom_key: Optional[bool] = None
    gemini_api_key: Optional[str] = None
