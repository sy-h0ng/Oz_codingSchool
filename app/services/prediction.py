import asyncio
from decimal import Decimal
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult
from app.repositories.ai_analysis_result import (
    create_result,
    get_result_by_record_and_model,
    list_results_by_record_id,
)
from app.repositories.medical_record import get_medical_record_by_id
from app.worker.model import predict_pneumonia

AI_MODEL_NAME = "SimpleCNN"
PROJECT_DIR = Path(__file__).resolve().parents[2]


async def predict_record(db: AsyncSession, record_id: int) -> AIAnalysisResult:
    """저장된 X-Ray로 예측하고, 같은 모델 결과가 있으면 재사용한다."""

    record = await get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")

    cached_result = await get_result_by_record_and_model(db, record_id, AI_MODEL_NAME)
    if cached_result is not None:
        return cached_result

    if not record.xray_images:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="예측에 사용할 X-Ray 이미지가 없습니다.",
        )

    # 현재 요구사항에서는 진료기록당 업로드된 첫 번째 X-Ray를 사용한다.
    image_url = record.xray_images[0].image_url
    image_path = PROJECT_DIR / image_url.lstrip("/")
    if not image_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="저장된 X-Ray 이미지 파일을 찾을 수 없습니다.",
        )

    # 모델 추론은 CPU 작업이므로 이벤트 루프를 막지 않도록 별도 스레드에서 수행한다.
    prediction = await asyncio.to_thread(predict_pneumonia, image_path)

    return await create_result(
        db,
        record_id=record_id,
        is_pneumonia=bool(prediction["is_pneumonia"]),
        confidence=Decimal(str(prediction["confidence"])),
        ai_model=AI_MODEL_NAME,
        heatmap_url=None,
    )


async def list_record_predictions(
    db: AsyncSession, record_id: int
) -> list[AIAnalysisResult]:
    if await get_medical_record_by_id(db, record_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="진료기록을 찾을 수 없습니다.")
    return await list_results_by_record_id(db, record_id)
