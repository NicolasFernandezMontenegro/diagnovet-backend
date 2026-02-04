import uuid
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from app.core.security import api_key_auth
from app.schemas.responses import ReportResponse, CreateReportResponse
from app.services.repository import ReportRepository
from app.services.document_ai import DocumentAIService
from app.services.storage import StorageService 
from app.core.dependencies import get_repo, get_storage_service


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
    dependencies=[Depends(api_key_auth)],
)

def get_document_ai_service() -> DocumentAIService:
    return DocumentAIService()

@router.post("", response_model=CreateReportResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    file: UploadFile = File(...),
    repo: ReportRepository = Depends(get_repo),
    doc_service: DocumentAIService = Depends(get_document_ai_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed."
        )

    try:
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        gcs_uri = await storage_service.upload_file(
            file_obj=file.file, 
            destination_blob_name=unique_filename,
            content_type=file.content_type
        )

        report = await doc_service.process_document(gcs_uri, storage_service)
        
        repo.save(report)
        
        return {
                "report_id": report.id,
                "status": "processed"
            }


    except Exception as e:
        print(f"Error processing report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=str(e)
        )

@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    repo: ReportRepository = Depends(get_repo),
    storage_service: StorageService = Depends(get_storage_service) 
):
    report = repo.get(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    
    
    public_urls = []
    for gs_uri in report.image_urls:
        try:
        
            parts = gs_uri.split("/")
            
            if len(parts) > 3:
                blob_name = "/".join(parts[3:])
                signed_url = storage_service.generate_signed_url(blob_name)
                public_urls.append(signed_url)
            else:
                public_urls.append(gs_uri)
        except Exception as e:
            print(f"Error generando signed URL: {e}")
            public_urls.append(gs_uri)

    report.image_urls = public_urls

    return {"report": report}