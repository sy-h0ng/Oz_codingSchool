from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIAnalysisResultResponse(BaseModel):
    id: int
    record_id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None = None
    ai_model: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
