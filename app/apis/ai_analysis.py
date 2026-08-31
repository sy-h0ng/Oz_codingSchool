from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ai_analysis import AIAnalysisResponse
from app.services.ai_analysis import list_analyses, predict

router = APIRouter(prefix="/api/v1", tags=["ai-analysis"])


@router.post(
    "/medical-records/{record_id}/predict",
    response_model=AIAnalysisResponse,
    summary="AI 폐렴 예측 수행 (REQ-PRED-001)",
)
async def predict_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """진료기록에 연결된 X-Ray 이미지로 폐렴 예측을 수행한다. 이미 같은 모델로
    예측한 결과가 있으면 재추론 없이 그 결과를 그대로 반환한다."""
    return await predict(db, current_user, record_id)


@router.get(
    "/medical-records/{record_id}/analyses",
    response_model=list[AIAnalysisResponse],
    summary="AI 예측 결과 목록 조회 (REQ-PRED-002)",
)
async def list_analyses_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await list_analyses(db, current_user, record_id)
