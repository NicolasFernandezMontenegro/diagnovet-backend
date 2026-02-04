import os
import asyncio
import json
import datetime
from google.cloud import storage
from google.auth import impersonated_credentials
from google.auth import default as auth_default
from app.core.config import get_settings

class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.bucket_name = self.settings.GCS_BUCKET_NAME
        
        # 1. Cargamos las credenciales del entorno
        self.credentials, self.project_id = auth_default()
        
        # 2. Cliente estándar para operaciones de datos (Upload/Read)
        self.client = storage.Client(credentials=self.credentials, project=self.project_id)
        
        # 3. Lógica de Cliente de Firma Inteligente
        self.service_account_email = self._get_sa_email()
        self.signing_client = self._initialize_signing_client()

    def _get_sa_email(self):
        """Detects the current Service Account email."""
        # PRIORIDAD 1: Forzar por variable de entorno (lo más seguro en Cloud Run)
        env_sa = os.getenv("SERVICE_ACCOUNT_EMAIL")
        if env_sa:
            return env_sa
            
        try:
            # PRIORIDAD 2: Intentar obtenerla del cliente
            email = self.client.get_service_account_email()
            # Si el email contiene 'gs-project-accounts', es la cuenta errónea de Google
            if "gs-project-accounts" in email:
                print(f"DEBUG: Detected internal GS account {email}, attempting fallback.")
                return None
            return email
        except Exception:
            return getattr(self.credentials, 'service_account_email', None)

    def _initialize_signing_client(self):
        """
        Decide cómo firmar basándose en el entorno.
        - Local con JSON: El cliente estándar ya puede firmar.
        - Cloud Run: Requiere impersonación para delegar a la API de IAM.
        """
        # Si tenemos una llave privada local (JSON), NO necesitamos impersonar
        if hasattr(self.credentials, 'signer') and self.credentials.signer:
            print("INFO: Local key detected. Using standard client for signing.")
            return self.client

        # Si estamos en Cloud Run (Token pero no llave privada)
        if self.service_account_email:
            print(f"INFO: Cloud environment detected. Using impersonation for: {self.service_account_email}")
            target_scopes = ["https://www.googleapis.com/auth/cloud-platform"]
            
            # Impersonamos para que la firma se delegue a la API de IAM
            im_creds = impersonated_credentials.Credentials(
                source_credentials=self.credentials,
                target_principal=self.service_account_email,
                target_scopes=target_scopes,
            )
            return storage.Client(credentials=im_creds, project=self.project_id)

        # Último recurso: usar el cliente base
        return self.client

    def generate_signed_url(self, blob_name: str, expiration_seconds: int = 3600) -> str:
        """Genera una URL firmada V4 detectando el mecanismo de firma óptimo."""
        try:
            bucket = self.signing_client.bucket(self.bucket_name)
            blob = bucket.blob(blob_name)

            return blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(seconds=expiration_seconds),
                method="GET",
                service_account_email=self.service_account_email
            )
        except Exception as e:
            # Si la firma falla, imprimimos el error y damos el fallback público
            print(f"WARNING: Signing failed: {e}")
            return f"https://storage.googleapis.com/{self.bucket_name}/{blob_name}"

    # --- Tus otros métodos se mantienen iguales ---
    async def upload_file(self, file_obj, destination_blob_name: str, content_type: str) -> str:
        return await asyncio.to_thread(self._upload_sync, file_obj, destination_blob_name, content_type)

    def _upload_sync(self, file_obj, destination_blob_name: str, content_type: str) -> str:
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(destination_blob_name)
        file_obj.seek(0)
        blob.upload_from_file(file_obj, content_type=content_type)
        return f"gs://{self.bucket_name}/{destination_blob_name}"

    async def list_files(self, prefix: str):
        return await asyncio.to_thread(self._list_files_sync, prefix)

    def _list_files_sync(self, prefix: str):
        bucket = self.client.bucket(self.bucket_name)
        return list(bucket.list_blobs(prefix=prefix))

    async def read_json_file(self, blob_name: str):
        return await asyncio.to_thread(self._read_json_sync, blob_name)

    def _read_json_sync(self, blob_name: str):
        bucket = self.client.bucket(self.bucket_name)
        blob = bucket.blob(blob_name)
        content = blob.download_as_text()
        return json.loads(content)