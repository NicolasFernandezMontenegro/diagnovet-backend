# Diagnovet Backend – Veterinary Medical Report Processing API

## Overview
Diagnovet Backend is a production-ready REST API designed to transform unstructured veterinary medical reports (PDF) into structured JSON data and securely accessible medical images. 

The system leverages **Google Document AI** for OCR, **Google Cloud Storage** for asset management, and **Google Firestore** for metadata persistence. It is built to handle **real-world variability** in document length and formatting.

The architecture prioritizes **deterministic behavior**, **explicit failure modes**, and **operational clarity**, avoiding opaque AI-only extraction pipelines.

## Key Features
* **Hybrid Ingestion:** Automatic failover from Online (Sync) to Batch (Async) processing for documents exceeding 30 pages.
* **Deterministic Parsing Engine:** RegEx-based extraction of Patient, Owner, Veterinarian, and Clinical data with noise filtering and collision prevention.
* **Image Asset Extraction:** Every PDF page is rendered and stored as a high-quality JPEG for reliable visual access (radiographs, ultrasounds).
* **Security First:**  
  * API Key authentication for all endpoints  
  * Private GCS buckets with **V4 Signed URLs** (HMAC-SHA256) for secure, time-limited image access
  * Identity-Based Signing: Utilizes IAM Impersonation (Service Account Token Creator) to generate Signed URLs in Cloud Run without storing sensitive JSON keys within the container environment.

* **Cloud-Native Scalability:** Stateless FastAPI service deployed on **Google Cloud Run**, scaling automatically with traffic.

## Tech Stack
* **Backend:** FastAPI (Python 3.11)
* **OCR / AI:** Google Document AI (OCR Processor)
* **Storage:** Google Cloud Storage
* **Database:** Google Firestore (NoSQL)
* **Deployment:** Docker + Google Cloud Run

---

## API Endpoints

### `POST /reports`
Uploads and processes a veterinary medical report.

**Request:**
* **Method:** `POST`
* **Content-Type:** `multipart/form-data`
* **Field:** `file` (The PDF report)
* **Header:** `X-API-Key: <your_key>`

**Response (201 Created):**

```json
{
  "report_id": "string",
  "status": "processed"
}
```

> Note: The POST endpoint is intentionally lightweight and returns only the generated `report_id`. The full structured report and image URLs can be retrieved via the `GET /reports/{report_id}` endpoint.


### `GET /reports/{report_id}`

Retrieves the structured data of a processed report.

**Behavior:**

* **Just-in-Time URL Generation**: URIs are stored as immutable gs:// paths in Firestore; the API generates ephemeral HTTPS signatures only upon request to ensure the principle of least privilege.

**Response (200 OK):**

```json
{
  "report": {
    "id": "string",
    "patient": {
      "name": "string",
      "species": "string",
      "breed": "string",
      "age": "string",
      "sex": "string"
    },
    "owner": {
      "name": "string",
      "contact": "string"
    },
    "veterinarian": {
      "name": "string",
      "clinic": "string"
    },
    "diagnosis": "string",
    "recommendations": "string",
    "image_urls": ["string"],
    "created_at": "2026-02-04T01:11:05Z"
  }
}
```

---

### Backend Logic & Design Choices

#### 1. Online → Batch Failover Strategy

Document AI limits online processing to 30 pages.

1. Attempt Online (`process_document`)

2. On `PAGE_LIMIT_EXCEEDED`, trigger Batch processing

3. Poll batch output, merge sharded JSON results from GCS

4. Continue parsing with a unified document model

This guarantees consistent behavior regardless of document size.

#### 2. Deterministic Parsing Engine

Instead of probabilistic extraction, the parser uses:

* **Anchored Regular Expressions**
Prevents accidental value capture across visual lines

* **Stop-Word Boundaries**
Ensures fields terminate correctly when multiple labels share a line

* **Section Reconstruction**
Combines findings and conclusions while filtering repeated headers/footers

This approach favors **predictability and debuggability** over raw recall.

#### 3. Image Handling Strategy

All pages are rendered and stored as images.

This guarantees:

* No false negatives from OCR layout detection

* Full visual access to original diagnostic material

* Safe delivery via signed URLs without exposing buckets

## Project Structure

```Plaintext
diagnovet-backend/
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── api/
│   │   └── routes.py         # POST /reports, GET /reports/{id}
│   ├── core/
│   │   ├── config.py         # Environment configuration
│   │   ├── security.py       # API key validation
│   │   └── dependencies.py  # Dependency injection
│   ├── schemas/
│   │   ├── domain.py         # Pydantic domain models
│   │   └── responses.py     # API response models
│   └── services/
│       ├── document_ai.py    # Sync/Batch OCR logic
│       ├── report_parser.py # Deterministic parser
│       ├── storage.py        # GCS & Signed URLs
│       └── repository.py    # Firestore persistence
├── tests/
│   ├── samples/sample_report.pdf
│   └── test_api.py           # End-to-end integration test
├── Dockerfile
└── requirements.txt
```
---

## Testing & Deployment

### Local Testing

```Bash
uvicorn app.main:app --reload
python3 tests/test_api.py --file tests/samples/sample_report.pdf --key secret123
```

The integration test mirrors the exact workflow expected from real API consumers.


## Live API (Cloud Run)

The API is deployed on **Google Cloud Run** and publicly accessible.

**Base URL:**

https://diagnovet-backend-758060382388.us-central1.run.app/


**Swagger UI:**

https://diagnovet-backend-758060382388.us-central1.run.app/docs


**Authentication:**
All endpoints are protected using an `x-api-key` header.

**Available endpoints:**
- `POST /reports` – Upload a veterinary PDF report
- `GET /reports/{id}` – Retrieve parsed report and extracted images
- `GET /health` – Health check

The service uses:
- Cloud Run (containerized FastAPI app)
- Cloud Storage (PDFs and extracted images)
- Cloud Document AI (OCR & layout parsing)
- Firestore (report persistence)


## Possible Improvements & Strategic Roadmap

To transition this system from a functional MVP to a high-scale clinical product, the following architectural and security enhancements are proposed:
### 1. Professional-Grade Security ("Security REAL")

  **Google Secret Manager Integration**: Move all sensitive credentials (API keys, service account emails) from environment variables to an encrypted vault. This allows for automated secret rotation and prevents exposure in logs or CI/CD pipelines.

  **Hashed API Key Management**: Transition to a multi-tenant authentication system where SHA-256 hashes of client keys are stored in Firestore. This enables individual revocation of access for different clinics without affecting the entire service.

  **Identity-Based Access Control**: Implement fine-grained IAM roles to further restrict the "Service Account Token Creator" permissions to specific resources, adhering to the principle of least privilege.

### 2. Event-Driven Scalability

  **Asynchronous Webhooks via Pub/Sub**: Decouple the Batch processing failover by utilizing Google Cloud Pub/Sub. Instead of the client waiting for a response or polling, the system will push a notification to a registered webhook once the diagnostic report is fully processed.

  **Dead Letter Queues (DLQ)**: Implementation of a retry and monitoring mechanism for documents that fail OCR or parsing, ensuring no medical data is lost during transient outages.

### 3. Data Integrity & Processing

  **Contextual Refinement Engine**: Implementation of a semantic processing layer to act as a clinical reasoning stage over the Regex extraction. This engine will normalize medical terminology and programmatically correct character-level inaccuracies (OCR typos) in pharmaceutical dosages and clinical nomenclature.

  **Strict Metadata Validation**: Enhancing Pydantic models with domain-specific validators for the veterinary field, such as species-specific age ranges and standardized formatting for clinical dates.