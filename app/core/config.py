from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    PROJECT_ID: str
    GCP_LOCATION: str
    DOCUMENT_AI_PROCESSOR_ID: str
    GCS_BUCKET_NAME: str
    API_KEY: str
    GOOGLE_APPLICATION_CREDENTIALS: str
    ENV: Literal["dev", "prod"] = "dev"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="forbid"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
