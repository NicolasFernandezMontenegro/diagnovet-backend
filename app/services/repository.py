from typing import Dict, Optional
from app.schemas.domain import Report


class ReportRepository:
    
    def __init__(self):
        self._reports: Dict[str, Report] = {}

    def save(self, report: Report) -> Report:
        self._reports[report.id] = report
        return report

    def get(self, report_id: str) -> Optional[Report]:
        return self._reports.get(report_id)
