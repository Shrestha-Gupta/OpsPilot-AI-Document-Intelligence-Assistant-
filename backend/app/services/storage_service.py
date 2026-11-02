"""
Supabase Storage service for uploading, retrieving, and deleting PDF files.
"""
import logging
from app.db.supabase import get_supabase
from app.config import get_settings
from app.core.exceptions import AppError

logger = logging.getLogger("opspilot.storage")


class StorageService:
    def __init__(self):
        self.settings = get_settings()
        self.bucket_name = self.settings.supabase_bucket_name

    def upload_file(self, path: str, file_bytes: bytes, content_type: str = "application/pdf") -> str:
        """
        Upload file bytes to Supabase Storage.
        Returns the storage path.
        """
        supabase = get_supabase()
        try:
            supabase.storage.from_(self.bucket_name).upload(
                path=path,
                file=file_bytes,
                file_options={"content-type": content_type, "upsert": "true"},
            )
            logger.info(f"Uploaded file to storage: {self.bucket_name}/{path}")
            return path
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise AppError(
                message=f"Storage upload failed: {str(e)}",
                status_code=500,
                error_code="STORAGE_UPLOAD_FAILED",
            )

    def download_file(self, path: str) -> bytes:
        """Download raw bytes from Supabase Storage."""
        supabase = get_supabase()
        try:
            return supabase.storage.from_(self.bucket_name).download(path)
        except Exception as e:
            logger.error(f"Failed to download file from storage: {e}")
            raise AppError(
                message=f"Storage download failed: {str(e)}",
                status_code=500,
                error_code="STORAGE_DOWNLOAD_FAILED",
            )

    def delete_file(self, path: str) -> None:
        """Delete a file from Supabase Storage."""
        supabase = get_supabase()
        try:
            supabase.storage.from_(self.bucket_name).remove([path])
            logger.info(f"Deleted file from storage: {self.bucket_name}/{path}")
        except Exception as e:
            logger.error(f"Failed to delete file from storage: {e}")
            # Non-blocking warning for cleanups
            pass


_storage_service: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
