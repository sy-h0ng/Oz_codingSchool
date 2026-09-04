FROM python:3.13-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml uv.lock ./
# AI worker에만 Torch/Pillow extra를 설치한다. FastAPI 이미지에는 포함되지 않는다.
RUN uv sync --frozen --no-dev --extra ai --no-install-project

COPY worker ./worker

CMD ["uv", "run", "--no-sync", "python", "-m", "worker.main"]
