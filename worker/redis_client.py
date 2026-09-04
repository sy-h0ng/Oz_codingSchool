"""AI 워커용 동기 Redis 클라이언트.

워커는 FastAPI 앱과 달리 요청 하나를 계속 블로킹(brpoplpush)해서 대기하는
단순한 반복문(worker/main.py)으로 동작하기 때문에 async 클라이언트가 필요 없다.
"""

from __future__ import annotations

import os

import redis

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
