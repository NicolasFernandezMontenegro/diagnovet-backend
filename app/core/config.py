import os
import requests
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

def get_project_id_from_metadata() -> Optional[str]:
    try:
        resp = requests.get(
            "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"},
            timeout=1,
        )
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None

class Settings(BaseSettings):

    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    PROJECT_ID: Optional[str] = None

    GCP_LOCATION: str
    DOCUMENT_AI_PROCESSOR_ID: str
    GCS_BUCKET_NAME: str
    API_KEY: str

    def resolved_project_id(self) -> str:
        if self.PROJECT_ID:
            return self.PROJECT_ID
        metadata_project = get_project_id_from_metadata()
        if metadata_project:
            return metadata_project
        raise RuntimeError(
            "PROJECT_ID not found. Set PROJECT_ID env var or run inside GCP."
        )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    config = Settings()
    
    if config.GOOGLE_APPLICATION_CREDENTIALS:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.GOOGLE_APPLICATION_CREDENTIALS
    
    try:
        os.environ["GOOGLE_CLOUD_PROJECT"] = config.resolved_project_id()
    except RuntimeError:
        pass

    return config

settings = get_settings()