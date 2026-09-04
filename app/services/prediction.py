import asyncio
import json
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis_client import get_redis
from app.models.ai_analysis_result import AIAnalysisResult
from app.repositories.ai_analysis_result import (
    create_result,
    get_result_by_record_and_model,
    list_results_by_record_id,
)
from app.repositories.medical_record import get_medical_record_by_id
AI_MODEL_NAME = "SimpleCNN"
PROJECT_DIR = Path(__file__).resolve().parents[2]
PREDICTION_QUEUE = "pneumonia:prediction:tasks"


def _task_key(record_id: int) -> str:
    return f"pneumonia:prediction:task:{record_id}:{AI_MODEL_NAME}"


def _result_key(task_id: str) -> str:
    return f"pneumonia:prediction:result:{task_id}"


def _result_channel(task_id: str) -> str:
    return f"pneumonia:prediction:result-channel:{task_id}"


async def _wait_for_worker_result(redis: Redis, task_id: str) -> dict[str, object]:
    """이 작업의 결과 채널을 구독한다. 이미 도착한 결과는 Redis 키에서 읽는다."""

    cached = await redis.get(_result_key(task_id))
    if cached:
        return json.loads(cached)

    pubsub = redis.pubsub()
    await pubsub.subscribe(_result_channel(task_id))
    try:
        async with asyncio.timeout(settings.PREDICTION_QUEUE_TIMEOUT_SECONDS):
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    return json.loads(message["data"])

                # 구독을 시작하기 전 worker가 결과를 보낸 아주 짧은 경쟁 상황도 보완한다.
                cached = await redis.get(_result_key(task_id))
                if cached:
                    return json.loads(cached)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI 예측 작업의 응답 시간이 초과되었습니다.",
        ) from exc
    finally:
        await pubsub.unsubscribe(_result_channel(task_id))
        await pubsub.aclose()


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

    redis = get_redis()
    task_key = _task_key(record_id)
    task_id = await redis.get(task_key)

    # 동일 진료기록/모델 요청은 같은 task_id를 공유한다.
    # SET NX EX는 여러 FastAPI 요청이 와도 작업을 한 번만 큐에 넣게 하는 Redis 락 역할이다.
    if task_id is None:
        new_task_id = str(uuid4())
        acquired = await redis.set(
            task_key,
            new_task_id,
            nx=True,
            ex=settings.PREDICTION_QUEUE_TIMEOUT_SECONDS,
        )
        if acquired:
            task_id = new_task_id
            task = {
                "task_id": task_id,
                "record_id": record_id,
                "image_path": str(image_path),
                "ai_model": AI_MODEL_NAME,
            }
            await redis.rpush(PREDICTION_QUEUE, json.dumps(task))
        else:
            task_id = await redis.get(task_key)

    if task_id is None:  # Redis 키가 만료된 아주 드문 경우에는 요청을 다시 시도하게 한다.
        raise HTTPException(status_code=503, detail="예측 작업 등록에 실패했습니다. 다시 시도해주세요.")

    prediction = await _wait_for_worker_result(redis, task_id)
    if prediction.get("status") != "success":
        # 실패 작업은 다음 요청에서 다시 등록될 수 있도록 task 키를 비운다.
        await redis.delete(task_key, _result_key(task_id))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(prediction.get("detail", "AI 예측 중 오류가 발생했습니다.")),
        )

    # 다른 요청이 먼저 결과를 저장했는지 한 번 더 확인한다.
    cached_result = await get_result_by_record_and_model(db, record_id, AI_MODEL_NAME)
    if cached_result is not None:
        return cached_result

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
