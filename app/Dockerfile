FROM python:3.13-slim

WORKDIR /

# healthcheck용 curl + asyncmy(C 확장) 빌드용 gcc 등 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv 패키지 매니저 설치
RUN pip install --no-cache-dir uv

# 의존성 정의 파일만 먼저 복사 (레이어 캐시 활용: 코드만 바뀌면 재설치 안 함)
COPY pyproject.toml uv.lock ./

# uv.lock에 고정된 버전 그대로 설치 (프로젝트 자체는 아직 없으므로 --no-install-project)
RUN uv sync --frozen --no-install-project

# 설치된 가상환경의 실행파일(uvicorn 등)을 PATH에 등록
ENV PATH="/.venv/bin:$PATH"

# 실제 애플리케이션 코드는 마지막에 복사
# (AI 추론은 Redis 큐를 통해 별도 ai-worker 컨테이너가 담당하므로, torch 등
# 무거운 의존성이 필요한 worker/ 는 이 이미지에 포함하지 않는다)
COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
