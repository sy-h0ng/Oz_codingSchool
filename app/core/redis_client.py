"""FastAPI 앱에서 AI 워커에게 예측 작업을 맡기고 결과를 기다리는 비동기 Redis 클라이언트.

흐름: (1) 결과를 받을 채널을 먼저 구독(subscribe)한 뒤, (2) 작업을 대기열(list)에
넣는다(publish/lpush). 순서를 반대로 하면 워커가 우리가 구독하기도 전에 결과를
publish해버려서 메시지를 영영 못 받는 경우가 생긴다.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import redis.asyncio as redis

from app.core.config import settings

PREDICTION_QUEUE_KEY = "prediction:queue"
RESULT_CHANNEL_PREFIX = "prediction:result:"
LOCK_KEY_PREFIX = "prediction:lock:"
LOCK_TTL_SECONDS = 30
DEFAULT_RESULT_TIMEOUT_SECONDS = 15

redis_client = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
)


async def request_prediction(
    image_path: str,
    model_name: str,
    *,
    dedup_key: str | None = None,
    timeout: float = DEFAULT_RESULT_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """AI 워커에 예측 작업을 요청하고, 워커가 publish하는 결과를 기다려서 반환한다.

    dedup_key를 주면(예: "record:{진료기록ID}:{모델명}") 같은 대상에 대해 거의
    동시에 여러 요청이 들어와도 워커에는 작업을 한 번만 넣고, 나머지 요청은 먼저
    들어간 작업의 결과를 같이 구독해서 기다린다.
    """
    lock_key = f"{LOCK_KEY_PREFIX}{dedup_key}" if dedup_key else None
    job_id = str(uuid.uuid4())
    is_owner = True

    if lock_key is not None:
        is_owner = bool(
            await redis_client.set(lock_key, job_id, nx=True, ex=LOCK_TTL_SECONDS)
        )
        if not is_owner:
            job_id = await redis_client.get(lock_key) or job_id

    result_channel = f"{RESULT_CHANNEL_PREFIX}{job_id}"
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(result_channel)
    # subscribe()가 돌려주는 "구독 확인" 메시지를 먼저 비워줘야 한다. 비우지 않으면
    # 바로 다음 get_message(timeout=...) 호출이 그 확인 메시지만 보고 timeout을
    # 기다리지 않은 채 곧장 None을 반환해버린다 (redis-py의 알려진 동작).
    await pubsub.get_message(timeout=1)
    try:
        if is_owner:
            payload = json.dumps(
                {
                    "job_id": job_id,
                    "image_path": image_path,
                    "model_name": model_name,
                    "result_channel": result_channel,
                }
            )
            await redis_client.lpush(PREDICTION_QUEUE_KEY, payload)

        message = await pubsub.get_message(
            ignore_subscribe_messages=True, timeout=timeout
        )
        if message is None:
            raise TimeoutError(f"AI 워커로부터 {timeout}초 내에 응답을 받지 못했습니다.")
        return json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(result_channel)
        await pubsub.aclose()
        if lock_key is not None and is_owner:
            await redis_client.delete(lock_key)
