from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.ai_analysis_result import (
    create_ai_analysis_result,
    get_ai_analysis_result_by_record_and_model,
    list_ai_analysis_results_by_record as repo_list_ai_analysis_results_by_record,
)
from app.repositories.medical_record import get_medical_record_by_id
from app.schemas.ai_analysis_result import AIAnalysisResultResponse
from app.services.medical_record import require_medical_record_access
from worker.model import MODEL_NAME, predict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 히트맵(Grad-CAM 등) 시각화는 아직 구현하지 않아 항상 빈 문자열을 저장한다.
# REQ-PRED-001 요구사항 상 heatmap_url은 선택 항목이다.
HEATMAP_URL_PLACEHOLDER = ""


async def predict_pneumonia(
    db: AsyncSession, current_user: User, record_id: int
) -> AIAnalysisResultResponse:
    require_medical_record_access(current_user)

    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")

    # 같은 모델로 이미 저장된 예측 결과가 있다면 추론을 다시 하지 않고 재사용한다.
    cached = await get_ai_analysis_result_by_record_and_model(db, record_id, MODEL_NAME)
    if cached is not None:
        return AIAnalysisResultResponse.model_validate(cached)

    if not record.xray_images:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "진료기록에 등록된 X-Ray 이미지가 없습니다."
        )
    latest_image = max(record.xray_images, key=lambda image: image.id)
    image_path = BASE_DIR / latest_image.image_url.removeprefix("/")
    image_bytes = image_path.read_bytes()

    is_pneumonia, confidence = predict(image_bytes)

    result = await create_ai_analysis_result(
        db,
        record_id=record_id,
        is_pneumonia=is_pneumonia,
        confidence=round(confidence * 100, 2),
        heatmap_url=HEATMAP_URL_PLACEHOLDER,
        ai_model=MODEL_NAME,
    )
    return AIAnalysisResultResponse.model_validate(result)


async def list_ai_analysis_results(
    db: AsyncSession, current_user: User, record_id: int
) -> list[AIAnalysisResultResponse]:
    require_medical_record_access(current_user)

    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")

    results = await repo_list_ai_analysis_results_by_record(db, record_id)
    return [AIAnalysisResultResponse.model_validate(result) for result in results]
