from fastapi import FastAPI, Depends
from app.core.security import api_key_auth

app = FastAPI(title="DiagnoVET Backend")


@app.get("/health", dependencies=[Depends(api_key_auth)])
def health():
    return {"status": "ok"}
