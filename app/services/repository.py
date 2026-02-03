from typing import Dict
from app.schemas.domain import Report


class InMemoryReportRepository:
    def __init__(self):
        self._data: Dict[str, Report] = {}

    def save(self, report: Report) -> None:
        self._data[report.id] = report

    def get(self, report_id: str) -> Report | None:
        return self._data.get(report_id)
