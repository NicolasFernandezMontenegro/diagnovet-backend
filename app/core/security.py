from fastapi import Header, HTTPException, status
from app.core.config import get_settings


def api_key_auth(x_api_key: str = Header(...)):
    settings = get_settings()

    if x_api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )
