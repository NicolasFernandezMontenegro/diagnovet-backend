import io
import uuid
import json 
from typing import List
from google.api_core.exceptions import InvalidArgument
from google.cloud import documentai_v1 as documentai
from google.api_core.client_options import ClientOptions
from app.core.config import get_settings
from app.services.report_parser import ReportParser
from app.services.storage import StorageService

class DocumentAIService:
    def __init__(self):
        self.settings = get_settings()
        self.client_options = ClientOptions(
            api_endpoint=f"{self.settings.GCP_LOCATION}-documentai.googleapis.com"
        )
        self.client = documentai.DocumentProcessorServiceClient(client_options=self.client_options)

    async def process_document(
        self, 
        gcs_uri: str, 
        storage_service: StorageService, 
        mime_type: str = "application/pdf"
    ):
        processor_name = self.client.processor_path(
            self.settings.resolved_project_id(),
            self.settings.GCP_LOCATION,
            self.settings.DOCUMENT_AI_PROCESSOR_ID
        )


        try:
            request = documentai.ProcessRequest(
                name=processor_name,
                skip_human_review=True,
                gcs_document=documentai.GcsDocument(
                    gcs_uri=gcs_uri,
                    mime_type=mime_type,
                ),
                process_options=documentai.ProcessOptions(
                    ocr_config=documentai.OcrConfig(enable_native_pdf_parsing=True)
                )
            )
            result = self.client.process_document(request=request)
            document = result.document
            print("Procesamiento Online exitoso")

        except InvalidArgument as e:
            if "PAGE_LIMIT_EXCEEDED" in str(e):
                print(f"Límite excedido ({e}). Cambiando a Batch Processing...")
                document = await self._process_batch(gcs_uri, processor_name, storage_service)
            else:
                raise e

        parser = ReportParser(document.text)
        report_data = parser.parse()

        image_urls = await self._extract_and_upload_images(document, storage_service)
        
        if hasattr(report_data, "image_urls"):
            report_data.image_urls = image_urls
        
        return report_data

    async def _process_batch(self, gcs_uri: str, processor_name: str, storage_service: StorageService):
        output_prefix = f"batch_results/{uuid.uuid4()}"
        output_gcs_uri = f"gs://{self.settings.GCS_BUCKET_NAME}/{output_prefix}"

        request = documentai.BatchProcessRequest(
            name=processor_name,
            input_documents=documentai.BatchDocumentsInputConfig(
                gcs_documents=documentai.GcsDocuments(
                    documents=[{"gcs_uri": gcs_uri, "mime_type": "application/pdf"}]
                )
            ),
            document_output_config=documentai.DocumentOutputConfig(
                gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
                    gcs_uri=output_gcs_uri
                )
            ),
        )

        operation = self.client.batch_process_documents(request=request)
        
        print("Esperando a que termine el Batch processing...")
        operation.result(timeout=180) 
        print("Batch terminado. Descargando resultados...")

        blobs = await storage_service.list_files(prefix=output_prefix)
        json_blobs = [b for b in blobs if b.name.endswith(".json")]
        json_blobs.sort(key=lambda x: x.name)

        full_text = ""
        all_pages = []
        combined_document = documentai.Document()

        for blob in json_blobs:
            json_data = await storage_service.read_json_file(blob.name)
            shard_doc = documentai.Document.from_json(json.dumps(json_data))
            
            if shard_doc.text:
                full_text += shard_doc.text
            if shard_doc.pages:
                all_pages.extend(shard_doc.pages)

        combined_document.text = full_text
        combined_document.pages.extend(all_pages)
        
        return combined_document

    async def _extract_and_upload_images(self, document, storage_service: StorageService) -> List[str]:
        urls = []
        
        for i, page in enumerate(document.pages):
            
            if page.image and page.image.content:
                try:
                    image_content = page.image.content
                    file_obj = io.BytesIO(image_content)
                    
                    folder_id = uuid.uuid4()
                    filename = f"images/{folder_id}/page_{i+1}.jpeg"
                    
                    gcs_uri = await storage_service.upload_file(
                        file_obj=file_obj,
                        destination_blob_name=filename,
                        content_type="image/jpeg"
                    )
                    urls.append(gcs_uri)
                except Exception as e:
                    print(f"Error procesando página {i+1}: {e}")
                    continue
        
        return urls