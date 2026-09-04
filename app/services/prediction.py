from __future__ import annotations

import uuid
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import request_prediction
from app.models.ai_analysis_result import AIAnalysisResult
from app.models.user import User
from app.repositories.ai_analysis_result import (
    create_result,
    get_result_by_record_and_model,
    list_results_by_record_id,
)
from app.repositories.medical_record import get_medical_record_by_id
from app.services.medical_record import require_medical_record_access

PROJECT_DIR = Path(__file__).resolve().parents[2]
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png"}
TMP_PREDICTION_DIR = PROJECT_DIR / "media" / "tmp_predictions"

# worker/model.py의 MODEL_NAME과 반드시 같아야 한다. torch를 설치하지 않는 fastapi
# 이미지에서 worker.model을 직접 import할 수 없어서 문자열로 중복 정의한다.
MODEL_NAME = "SimpleCNN-sample-v1"


def _latest_xray_image_path(record) -> Path:
    if not record.xray_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="예측에 사용할 X-Ray 이미지가 없습니다.",
        )

    latest_image = max(record.xray_images, key=lambda image: image.id)
    image_path = PROJECT_DIR / latest_image.image_url.lstrip("/")
    if not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 X-Ray 이미지 파일을 찾을 수 없습니다.",
        )
    return image_path


async def _request_prediction_or_502(image_path: str, *, dedup_key: str | None = None) -> dict:
    try:
        prediction = await request_prediction(image_path, MODEL_NAME, dedup_key=dedup_key)
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc

    if prediction.get("error"):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI 예측 중 오류가 발생했습니다: {prediction['error']}",
        )
    return prediction


async def predict_record(
    db: AsyncSession, current_user: User, record_id: int
) -> AIAnalysisResult:
    require_medical_record_access(current_user)

    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")

    cached_result = await get_result_by_record_and_model(db, record_id, MODEL_NAME)
    if cached_result is not None:
        return cached_result

    image_path = _latest_xray_image_path(record)
    prediction = await _request_prediction_or_502(
        str(image_path), dedup_key=f"record:{record_id}:{MODEL_NAME}"
    )

    return await create_result(
        db,
        record_id=record_id,
        is_pneumonia=bool(prediction["is_pneumonia"]),
        confidence=Decimal(str(prediction["confidence"])),
        ai_model=str(prediction["ai_model"]),
        heatmap_url=prediction.get("heatmap_url"),
    )


async def predict_uploaded_xray(current_user: User, xray_image: UploadFile) -> dict:
    require_medical_record_access(current_user)

    if xray_image.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="흉부 X-Ray 이미지는 JPEG 또는 PNG 형식만 업로드할 수 있습니다.",
        )

    image_bytes = await xray_image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="업로드된 이미지 파일이 비어 있습니다.",
        )

    # 진료기록에 속하지 않은 즉석 업로드라 저장된 파일이 없다. AI 워커가 파일
    # 경로로만 이미지를 읽을 수 있으므로, fastapi/ai-worker가 공유하는 media
    # 볼륨에 임시로 저장했다가 예측이 끝나면 지운다.
    TMP_PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(xray_image.filename or "").suffix or ".jpg"
    tmp_path = TMP_PREDICTION_DIR / f"{uuid.uuid4()}{extension}"
    tmp_path.write_bytes(image_bytes)

    try:
        prediction = await _request_prediction_or_502(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)

    return {
        "is_pneumonia": bool(prediction["is_pneumonia"]),
        "confidence": float(prediction["confidence"]),
        "heatmap_url": prediction.get("heatmap_url"),
        "ai_model": str(prediction["ai_model"]),
    }


async def list_record_predictions(
    db: AsyncSession, current_user: User, record_id: int
) -> list[AIAnalysisResult]:
    require_medical_record_access(current_user)

    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")

    return await list_results_by_record_id(db, record_id)
