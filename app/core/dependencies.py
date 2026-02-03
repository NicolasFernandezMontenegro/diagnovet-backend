from app.services.repository import ReportRepository

_repo = ReportRepository()

def get_repo() -> ReportRepository:
    return _repo
