from __future__ import annotations

from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.user import User
from app.repositories.ai_analysis import (
    create_analysis,
    get_analysis_by_record_and_model,
    list_analyses_by_record as repo_list_analyses_by_record,
)
from app.repositories.medical_record import get_medical_record_by_id
from app.schemas.ai_analysis import AIAnalysisResponse
from app.services.medical_record import require_medical_record_access
from worker.model import MODEL_NAME, predict_pneumonia

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _latest_xray_image_url(record: MedicalRecord) -> str | None:
    if not record.xray_images:
        return None
    latest = max(record.xray_images, key=lambda image: image.id)
    return latest.image_url


async def _get_record_or_404(db: AsyncSession, record_id: int) -> MedicalRecord:
    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")
    return record


async def predict(db: AsyncSession, current_user: User, record_id: int) -> AIAnalysisResponse:
    require_medical_record_access(current_user)
    record = await _get_record_or_404(db, record_id)

    # 이미 같은 모델로 예측한 결과가 있으면 재추론 없이 그대로 반환 (REQ-PRED-001)
    cached = await get_analysis_by_record_and_model(db, record_id, MODEL_NAME)
    if cached is not None:
        return AIAnalysisResponse.model_validate(cached)

    xray_url = _latest_xray_image_url(record)
    if xray_url is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="연결된 X-Ray 이미지가 없습니다."
        )

    image_path = BASE_DIR / xray_url.lstrip("/")
    image_bytes = image_path.read_bytes()

    is_pneumonia, confidence = predict_pneumonia(image_bytes)

    analysis = await create_analysis(
        db,
        record_id=record_id,
        is_pneumonia=is_pneumonia,
        confidence=confidence,
        # 실제 히트맵 생성 기능은 없어서, 원본 X-Ray URL을 그대로 재사용한다 (설계서 1.2 참고).
        heatmap_url=xray_url,
        ai_model=MODEL_NAME,
    )
    return AIAnalysisResponse.model_validate(analysis)


async def list_analyses(
    db: AsyncSession, current_user: User, record_id: int
) -> list[AIAnalysisResponse]:
    require_medical_record_access(current_user)
    await _get_record_or_404(db, record_id)

    analyses = await repo_list_analyses_by_record(db, record_id)
    return [AIAnalysisResponse.model_validate(analysis) for analysis in analyses]
