from pydantic import BaseModel
from app.models.recommendation import ItemType
from typing import Optional
from uuid import UUID
from datetime import datetime


class RecommendationCreate(BaseModel):
    user_id: UUID
    item_id: int
    item_type: ItemType
    score: Optional[float] = 0.0
    source_model: Optional[str] = "baseline"

class RecommendationRead(RecommendationCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime