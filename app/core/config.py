from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    env: str = "dev"
    project_id: str
    gcp_location: str = "us"
    document_ai_processor_id: str
    gcs_bucket_name: str
    api_key: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8"
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
