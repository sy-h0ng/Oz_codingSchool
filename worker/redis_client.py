"""AI worker에서 사용하는 동기 Redis 클라이언트."""

from __future__ import annotations

import os

from redis import Redis


def get_redis() -> Redis:
    """BLPOP과 publish에 쓸 동기 Redis 연결을 만든다."""

    return Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True,
    )
