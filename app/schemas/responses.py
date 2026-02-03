from pydantic import BaseModel
from app.schemas.domain import Report


class ReportResponse(BaseModel):
    report: Report
