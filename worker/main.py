"""Redis Task Queue를 소비해 폐렴 예측 후 결과를 Pub/Sub으로 보내는 worker."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from worker.model import predict_pneumonia
from worker.redis_client import get_redis

TASK_QUEUE = "pneumonia:prediction:tasks"
RESULT_TTL_SECONDS = 300

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def _result_key(task_id: str) -> str:
    return f"pneumonia:prediction:result:{task_id}"


def _result_channel(task_id: str) -> str:
    return f"pneumonia:prediction:result-channel:{task_id}"


def run_worker() -> None:
    redis = get_redis()
    logger.info("AI worker started; waiting for queue=%s", TASK_QUEUE)

    while True:
        # BLPOP은 여러 worker가 동시에 떠 있어도 하나의 task를 한 worker에게만 준다.
        # timeout=0은 Redis가 새 작업이 올 때까지 계속 기다린다는 뜻이다.
        # 짧은 socket timeout으로 worker가 종료되는 것을 막는다.
        item = redis.blpop(TASK_QUEUE, timeout=0)

        _, raw_task = item
        task = json.loads(raw_task)
        task_id = task["task_id"]
        try:
            image_path = Path(task["image_path"])
            if not image_path.is_file():
                raise FileNotFoundError(f"X-Ray 이미지가 없습니다: {image_path}")
            prediction = predict_pneumonia(image_path)
            result: dict[str, object] = {"status": "success", **prediction}
            logger.info("prediction completed task_id=%s", task_id)
        except Exception as exc:  # 한 작업 실패가 worker 전체 종료로 이어지면 안 된다.
            logger.exception("prediction failed task_id=%s", task_id)
            result = {"status": "error", "detail": str(exc)}

        encoded_result = json.dumps(result)
        # Pub/Sub 메시지를 놓친 FastAPI 요청도 result key에서 결과를 읽을 수 있게 한다.
        redis.set(_result_key(task_id), encoded_result, ex=RESULT_TTL_SECONDS)
        redis.publish(_result_channel(task_id), encoded_result)


if __name__ == "__main__":
    run_worker()
