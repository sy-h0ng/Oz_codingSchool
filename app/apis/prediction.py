from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ai_analysis_result import AIAnalysisResultResponse
from app.services.prediction import list_record_predictions, predict_record

router = APIRouter(prefix="/api/v1/medical-records", tags=["predictions"])


@router.post(
    "/{record_id}/predict",
    response_model=AIAnalysisResultResponse,
    status_code=status.HTTP_200_OK,
    summary="AI 모델 활용 폐렴 예측 (REQ-PRED-001)",
)
async def predict_pneumonia_api(
    record_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await predict_record(db, current_user, record_id)


@router.get(
    "/{record_id}/analyses",
    response_model=list[AIAnalysisResultResponse],
    summary="AI 모델 활용 폐렴 예측 결과 조회 (REQ-PRED-002)",
)
async def list_prediction_results_api(
    record_id: int = Path(..., ge=1),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    return await list_record_predictions(db, current_user, record_id)
