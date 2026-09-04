"""AI 예측 작업을 Redis 대기열(prediction:queue)에서 꺼내와 처리하는 워커.

- `BRPOPLPUSH queue -> processing`: 대기열에서 작업을 꺼내는 동시에 "처리 중"
  목록에 원자적으로(atomic) 옮겨 담는다. 여러 워커 프로세스가 동시에 떠 있어도
  BRPOPLPUSH는 원자적이라 같은 작업을 두 워커가 동시에 집어가는 일이 없다
  (다중 워커 환경에서의 안전한 작업 분배).
- 처리가 끝나면(성공/실패 무관) processing 목록에서 그 작업을 지운다.
- 워커가 시작될 때, 이전에 비정상 종료한 워커가 processing에 남겨둔 작업을
  대기열로 되돌린다 (비정상 종료 시 미완료 작업 복구, 선택 요구사항).
"""

from __future__ import annotations

import json
import logging
import os
import socket

from redis.exceptions import TimeoutError as RedisTimeoutError

from worker.model import predict_pneumonia
from worker.redis_client import redis_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")
logger = logging.getLogger(__name__)

QUEUE_KEY = "prediction:queue"
# 모든 워커가 공유하는 "처리 중" 목록. 워커별로 나누지 않고 하나로 공유해야
# 시작 시점에 "지금 이 목록에 남아있는 건 죽은 워커의 작업"이라고 단순하게
# 판단해서 복구할 수 있다 (아주 드물게 다른 워커가 막 집어간 작업과 타이밍이
# 겹치면 살아있는 작업까지 되돌릴 수 있다는 트레이드오프가 있지만, 예측 작업은
# 다시 수행해도 안전(idempotent)하므로 과제 규모에서는 허용 가능한 단순화다).
PROCESSING_KEY = "prediction:processing"
POP_TIMEOUT_SECONDS = 5


def recover_orphaned_jobs() -> None:
    while True:
        job = redis_client.rpoplpush(PROCESSING_KEY, QUEUE_KEY)
        if job is None:
            break
        logger.warning("복구: 이전 워커가 처리 중이던 작업을 대기열로 되돌림 - %s", job)


def handle_job(raw_job: str) -> None:
    job = json.loads(raw_job)
    job_id = job["job_id"]
    image_path = job["image_path"]
    result_channel = job["result_channel"]

    logger.info("작업 시작: job_id=%s image_path=%s", job_id, image_path)
    try:
        prediction = predict_pneumonia(image_path)
        result = {
            "job_id": job_id,
            "is_pneumonia": prediction["is_pneumonia"],
            "confidence": prediction["confidence"],
            "ai_model": prediction["ai_model"],
            "heatmap_url": None,
            "error": None,
        }
    except Exception as exc:  # noqa: BLE001 - 실패도 결과로 알려줘야 요청 쪽이 타임아웃까지 안 기다림
        logger.exception("예측 실패: job_id=%s", job_id)
        result = {"job_id": job_id, "error": str(exc)}

    redis_client.publish(result_channel, json.dumps(result))
    logger.info("작업 완료: job_id=%s", job_id)


def main() -> None:
    worker_name = f"{socket.gethostname()}-{os.getpid()}"
    logger.info("AI 워커 시작 (%s)", worker_name)
    recover_orphaned_jobs()

    while True:
        try:
            job = redis_client.brpoplpush(QUEUE_KEY, PROCESSING_KEY, timeout=POP_TIMEOUT_SECONDS)
        except RedisTimeoutError:
            # redis-py의 블로킹 명령에서 서버가 "작업 없음" 응답을 보내기 직전에
            # 클라이언트 소켓이 먼저 타임아웃되는 레이스 컨디션이 있다. 이 경우도
            # 그냥 "이번엔 작업이 없었다"로 보고 다음 반복으로 넘어간다.
            continue
        if job is None:
            continue
        try:
            handle_job(job)
        finally:
            redis_client.lrem(PROCESSING_KEY, 1, job)


if __name__ == "__main__":
    main()
