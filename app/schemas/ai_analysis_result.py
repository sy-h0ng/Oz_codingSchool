from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIAnalysisResultResponse(BaseModel):
    """AI 폐렴 예측 실행 및 조회에 사용하는 응답 형식"""

    id: int
    record_id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None
    ai_model: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
