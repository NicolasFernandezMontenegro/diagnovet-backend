import os
import asyncio
import json
from google.cloud import storage


class StorageService:
    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "diagnovet-bucket")
        self.client = storage.Client()

    async def upload_file(
        self,
        file_obj,
        destination_blob_name: str,
        content_type: str,
    ) -> str:
        return await asyncio.to_thread(
            self._upload_sync,
            file_obj,
            destination_blob_name,
            content_type,
        )

    def _upload_sync(
        self,
        file_obj,
        destination_blob_name: str,
        content_type: str,
    ) -> str:
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
