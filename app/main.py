from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from app.core.security import api_key_auth
from app.api.routes import router as report_router
from app.services.firestore_repository import FirestoreReportRepository

app = FastAPI(title="DiagnoVET Backend")

repo = FirestoreReportRepository()

app.include_router(report_router)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", dependencies=[Depends(api_key_auth)])
def health():
    return {"status": "ok"}
