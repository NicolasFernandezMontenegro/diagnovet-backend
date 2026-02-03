from app.services.repository import ReportRepository
from app.services.repository import ReportRepository
from app.services.storage import StorageService


def get_storage_service() -> StorageService:
    return StorageService()

def get_repo() -> ReportRepository:
    from app.main import repo
    return repo
