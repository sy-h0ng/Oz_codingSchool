from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_USER: str = "root"
    DB_PASSWORD: str = "password1234"
    DB_HOST: str = "localhost"
    DB_PORT: str = "3306"
    DB_NAME: str = "ai_health"

    # Redis는 FastAPI와 AI worker 사이에서 작업을 전달하고 결과를 받는 통로다.
    # 로컬 실행 시에는 localhost, Docker Compose 실행 시에는 redis 서비스 이름을 사용한다.
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    PREDICTION_QUEUE_TIMEOUT_SECONDS: int = 90

    SECRET_KEY: str = "dev-only-change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }


settings = Settings()
