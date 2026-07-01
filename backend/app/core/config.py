import os
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Semantic Debt Mapper"
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://sdm:sdm@localhost:5432/sdm"
    )
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    API_KEY: str
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
    )


settings = Settings()
