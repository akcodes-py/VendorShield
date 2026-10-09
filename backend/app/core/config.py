"""App config. WHY: one place for env secrets, avoids hardcoding."""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/vendorshield"
    TEST_DATABASE_URL: str = "sqlite:///:memory:"
    JWT_SECRET: str = "change-me-to-32-random-chars-minimum"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7
    UPLOAD_DIR: str = "backend/uploads"
    MAX_UPLOAD_MB: int = 10
    AI_SUMMARY_ENABLED: bool = False
    GEMINI_API_KEY: str = ""

    class Meta:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
