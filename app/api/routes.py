from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import api_key_auth
from app.schemas.responses import ReportResponse
from app.services.repository import ReportRepository
from app.services.document_ai import DocumentAIService
from app.core.dependencies import get_repo


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(api_key_auth)],
)


def get_document_ai_service() -> DocumentAIService:
    return DocumentAIService()


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report(
    gcs_uri: str,
    repo: ReportRepository = Depends(get_repo),
    service: DocumentAIService = Depends(get_document_ai_service),
):
    report = service.process_document(gcs_uri)
    repo.save(report)
    return {"report": report}


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    repo: ReportRepository = Depends(get_repo),
):
    report = repo.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return {"report": report}

