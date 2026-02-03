from google.cloud import documentai_v1 as documentai
from google.cloud import storage
from google.api_core.client_options import ClientOptions
from app.core.config import get_settings
from app.services.report_parser import ReportParser

import uuid


class DocumentAIService:
    def __init__(self):
        self.settings = get_settings()

        client_options = ClientOptions(
            api_endpoint=f"{self.settings.GCP_LOCATION}-documentai.googleapis.com"
        )

        self.client = documentai.DocumentProcessorServiceClient(
            client_options=client_options
        )

        self.storage_client = storage.Client()

    def upload_to_gcs(self, file_bytes: bytes, content_type: str) -> str:
        bucket = self.storage_client.bucket(self.settings.GCS_BUCKET_NAME)

        blob_name = f"uploads/{uuid.uuid4()}.pdf"
        blob = bucket.blob(blob_name)

        blob.upload_from_string(
            file_bytes,
            content_type=content_type
        )

        return f"gs://{self.settings.GCS_BUCKET_NAME}/{blob_name}"

    def process_document(self, gcs_uri: str, mime_type: str = "application/pdf"):
        processor_name = self.client.processor_path(
            self.settings.PROJECT_ID,
            self.settings.GCP_LOCATION,
            self.settings.DOCUMENT_AI_PROCESSOR_ID
        )

        request = documentai.ProcessRequest(
            name=processor_name,
            skip_human_review=True,
            gcs_document=documentai.GcsDocument(
                gcs_uri=gcs_uri,
                mime_type=mime_type,
            ),
            process_options=documentai.ProcessOptions(
                ocr_config=documentai.OcrConfig(
                    enable_native_pdf_parsing=True
                )
            )
        )

        result = self.client.process_document(request=request)
        document = result.document

        parser = ReportParser(document.text)
        return parser.parse()





