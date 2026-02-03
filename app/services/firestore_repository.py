from google.cloud import firestore
from app.schemas.domain import Report
from app.services.repository import ReportRepository

class FirestoreReportRepository(ReportRepository):
    def __init__(self):
        self.client = firestore.Client()
        self.collection = self.client.collection("reports")

    def save(self, report: Report) -> Report:
        self.collection.document(report.id).set(
            report.model_dump(mode="json")
        )
        return report

    def get(self, report_id: str) -> Report | None:
        doc = self.collection.document(report_id).get()
        if not doc.exists:
            return None
        return Report(**doc.to_dict())
