from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AIAnalysisResultResponse(BaseModel):
    id: int
    record_id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str
    ai_model: str
    created_at: datetime

    class Config:
        from_attributes = True
