from pydantic import BaseModel
from app.schemas.domain import Report

class CreateReportResponse(BaseModel):
    report_id: str
    status: str

class ReportResponse(BaseModel):
    report: Report
