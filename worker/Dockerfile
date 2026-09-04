FROM python:3.13-slim

WORKDIR /

# torch 등 빌드에 필요한 gcc 등 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv 패키지 매니저 설치
RUN pip install --no-cache-dir uv

# 의존성 정의 파일만 먼저 복사 (레이어 캐시 활용: 코드만 바뀌면 재설치 안 함)
COPY pyproject.toml uv.lock ./

# 기본 의존성 + ai extras(torch/numpy/pillow)까지 설치
RUN uv sync --frozen --no-install-project --extra ai

# 설치된 가상환경의 실행파일을 PATH에 등록
ENV PATH="/.venv/bin:$PATH"

# worker 코드만 복사 (app/ 은 필요 없음 — fastapi 쪽과 완전히 분리된 프로세스)
COPY worker ./worker

CMD ["python", "-m", "worker.main"]
