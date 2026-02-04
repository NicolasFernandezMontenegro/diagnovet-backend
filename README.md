# Diagnovet Backend – Veterinary Medical Report Processing API

## Overview
Diagnovet Backend is a production-ready REST API designed to transform unstructured veterinary medical reports (PDF) into structured JSON data and securely accessible medical images. 

The system leverages **Google Document AI** for OCR, **Google Cloud Storage** for asset management, and **Google Firestore** for metadata persistence. It is built to handle real-world variability in document length and formatting.

The system is designed with deterministic behavior and clear failure modes, prioritizing reliability over opaque AI-only extraction.

## Key Features
* **Hybrid Ingestion:** Automatic failover from Online (Sync) to Batch (Async) processing for documents exceeding 30 pages.
* **Deterministic Parsing:** A robust RegEx-based engine that extracts Patient, Owner, and Clinical data while filtering out noise and metadata headers.
* **Asset Management:** Automatic extraction of all PDF pages as high-quality JPEGs.
* **Security First:**  
  * API Key authentication for all endpoints  
  * Private GCS buckets with **V4 Signed URLs** (HMAC-SHA256) for secure, time-limited image access

* **Scalability:** Stateless design deployed on **Google Cloud Run**, scaling automatically based on demand.

## Tech Stack
* **Backend:** FastAPI (Python 3.11)
* **OCR / AI:** Google Document AI (OCR Processor)
* **Storage:** Google Cloud Storage
* **Database:** Google Firestore (NoSQL)
* **Deployment:** Google Cloud Run / Docker

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
    "image_urls": [
      "string"
    ],
    "created_at": "2026-02-04T01:11:05.929Z"
  }
}
```

> Note: Image paths are stored internally as `gs://` URIs and converted to HTTPS Signed URLs when retrieved via `GET /reports/{id}`.


### `GET /reports/{report_id}`

Retrieves the structured data of a processed report.

**Behavior:**

* Transforms internal `gs://` paths into public HTTPS Signed URLs.

* Links expire automatically after 1 hour.

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
    "image_urls": [
      "string"
    ],
    "created_at": "2026-02-04T01:11:05.919Z"
  }
}
```

---

### Backend Logic & Design Choices

#### 1. Failover Strategy (Online → Batch)

Document AI restricts online processing to 30 pages. To ensure reliability for long clinical histories:

1. The system attempts an Online Process.

2. If a `PAGE_LIMIT_EXCEEDED` error occurs, it triggers a Batch Job.

3. It polls/waits for the Batch result, merges the sharded JSON outputs from GCS, and proceeds with the extraction.

#### 2. Deterministic Parsing Engine

Instead of basic string matching, the `ReportParser` uses:

- **Anchored Regex**: Matches patterns only at the start of lines to avoid "eating" descriptions as values.

- **Stop Words**: Uses subsequent labels (e.g., "Sexo:", "Edad:") to terminate the capture of the previous field, preventing data merging.

- **Section Reconstruction**: Merges "Findings" and "Conclusions" while ignoring repetitive footers (e.g., "Dr. Martin Vittaz", "Página X").

#### 3. Image Handling

The system renders and uploads every page as an image. This design choice ensures that even if the OCR fails to label a specific region as a "visual element", the veterinarian can still view the original ultrasound or radiograph capture through the API.

## Project Structure

```Plaintext
diagnovet-backend/
├── app/
│   ├── main.py               # Entry point
│   ├── api/
│   │   └── routes.py         # POST and GET logic
│   ├── core/
│   │   ├── config.py         # Env vars (GCP_PROJECT, BUCKET, etc.)
│   │   ├── security.py       # API Key validation
│   │   └── dependencies.py   # Service singletons
│   ├── schemas/
│   │   ├── domain.py         # Pydantic models (Report, Patient)
│   │   └── responses.py      # API Response models
│   └── services/
│       ├── document_ai.py    # Sync/Batch logic & Image extraction
│       ├── report_parser.py  # Regex Engine
│       ├── storage.py        # GCS uploads & Signed URLs
│       └── repository.py     # Firestore CRUD
├── tests/
│   └── samples/
│       └── sample_report.pdf # Sample PDF for testing
│   └── test_api.py           # E2E Integration test
├── Dockerfile                # Python 3.11-slim
└── requirements.txt
```
---

## Testing & Deployment

### Local Test

1. Set up your `.env` with GCP credentials.

2. Run the server: `uvicorn app.main:app --reload`

3. Execute the E2E test:

```Bash
python3 tests/test_api.py --file "tests/samples/sample_report.pdf" --key "secret123"
```
The integration test reflects the exact workflow expected from API consumers and evaluators.

### Cloud Run Deployment

Deployed using a Service Account with `Storage Object Admin`, `Datastore User`, and `Document AI User` roles. This eliminates the need for local `.json` key files, following GCP security best practices. This setup follows the principle of least privilege and production-grade GCP deployment practice.


### Possible Improvements

- **Async Webhooks**: Convert the Batch failover into a truly asynchronous process using Pub/Sub.

- **LLM Refinement**: Use a small LLM (like Gemini Flash) to refine the Regex-extracted text.

- **Metadata Validation**: Add stricter Pydantic validators for dates and species.