from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ai_analysis_result import AIAnalysisResultResponse
from app.services.ai_analysis_result import list_ai_analysis_results, predict_pneumonia

router = APIRouter(prefix="/api/v1", tags=["ai-analysis"])


@router.post(
    "/medical-records/{record_id}/predict",
    response_model=AIAnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 모델 활용 폐렴 예측 (REQ-PRED-001)",
)
async def predict_pneumonia_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """진료기록에 저장된 최신 X-Ray 이미지로 폐렴 예측을 수행한다. 이미 같은
    모델로 저장된 예측 결과가 있으면 재추론 없이 해당 결과를 반환한다."""
    return await predict_pneumonia(db, current_user, record_id)


@router.get(
    "/medical-records/{record_id}/analyses",
    response_model=list[AIAnalysisResultResponse],
    summary="AI 모델 활용 폐렴 예측 결과 조회 (REQ-PRED-002)",
)
async def list_ai_analysis_results_api(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    """해당 진료기록에 대해 수행된 모든 AI 예측 결과 목록을 조회한다."""
    return await list_ai_analysis_results(db, current_user, record_id)
