"""FastAPI에서 사용하는 비동기 Redis 연결 도구."""

from __future__ import annotations

from redis.asyncio import Redis

from app.core.config import settings

_redis_client: Redis | None = None


def get_redis() -> Redis:
    """앱 프로세스마다 Redis 연결 객체를 하나만 만들어 재사용한다."""

    global _redis_client
    if _redis_client is None:
        _redis_client = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """FastAPI 종료 시 열린 Redis 연결을 안전하게 닫는다."""

    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
