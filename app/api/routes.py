from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import api_key_auth
from app.schemas.domain import Report
from app.schemas.responses import ReportResponse
from app.services.repository import InMemoryReportRepository
from app.utils.ids import generate_id
from datetime import datetime, timezone

router = APIRouter(
    prefix="/reports",
    dependencies=[Depends(api_key_auth)]
)

repository = InMemoryReportRepository()


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def create_report():
    report = Report(
        id=generate_id(),
        patient={},
        owner={},
        veterinarian={},
        created_at=datetime.now(timezone.utc)
    )

    repository.save(report)
    return {"report": report}


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(report_id: str):
    report = repository.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return {"report": report}
