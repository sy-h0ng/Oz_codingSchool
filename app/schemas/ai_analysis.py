from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AIAnalysisResponse(BaseModel):
    id: int
    record_id: int
    is_pneumonia: bool
    confidence: Decimal
    heatmap_url: str
    ai_model: str
    created_at: datetime

    class Config:
        from_attributes = True
