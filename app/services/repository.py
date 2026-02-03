from abc import ABC, abstractmethod
from app.schemas.domain import Report

class ReportRepository(ABC):

    @abstractmethod
    def save(self, report: Report) -> Report:
        pass

    @abstractmethod
    def get(self, report_id: str) -> Report | None:
        pass


"""class InMemoryReportRepository(ReportRepository):
    def __init__(self):
        self._store: dict[str, Report] = {}

    def save(self, report: Report) -> Report:
        self._store[report.id] = report
        return report

    def get(self, report_id: str) -> Report | None:
        return self._store.get(report_id)"""
