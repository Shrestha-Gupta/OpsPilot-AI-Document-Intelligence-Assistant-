"""
Document API endpoints:
- Upload PDFs (with background processing)
- List documents
- Get document details
- Poll document status
- Delete document
- Get suggested questions
"""
import uuid
import re
import logging
from typing import List
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Path

from app.config import get_settings
from app.core.exceptions import AppError
from app.schemas.document import (
    DocumentResponse,
    DocumentStatusResponse,
    DocumentUploadResponse,
    SuggestedQuestionsResponse,
)
from app.services.document_service import get_document_service
from app.services.storage_service import get_storage_service
from app.services.rag_service import get_rag_service

router = APIRouter(prefix="/documents", tags=["Documents"])
logger = logging.getLogger("opspilot.api.documents")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal and invalid characters."""
    clean = re.sub(r"[^\w\s.-]", "", filename).strip()
    return clean or "document.pdf"


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
):
    """
    Upload one or multiple PDF documents.
    Validates file sizes, uploads to Supabase Storage, registers in DB,
    and dispatches background extraction & indexing.
    """
    settings = get_settings()
    doc_service = get_document_service()
    storage_service = get_storage_service()

    if not files:
        raise AppError("No files provided", status_code=400, error_code="NO_FILES")

    if len(files) > settings.max_files_per_upload:
        raise AppError(
            f"Maximum {settings.max_files_per_upload} files allowed per upload",
            status_code=400,
            error_code="TOO_MANY_FILES",
        )

    created_documents: List[DocumentResponse] = []

    for file in files:
        original_name = file.filename or "document.pdf"
        if not original_name.lower().endswith(".pdf"):
            raise AppError(
                f"File '{original_name}' is not a PDF. Only PDF files are supported.",
                status_code=400,
                error_code="INVALID_FILE_TYPE",
            )

        content = await file.read()
        file_size = len(content)

        if file_size > settings.max_file_size_bytes:
            raise AppError(
                f"File '{original_name}' exceeds maximum allowed size of {settings.max_file_size_mb}MB",
                status_code=400,
                error_code="FILE_TOO_LARGE",
            )

        if file_size == 0:
            raise AppError(
                f"File '{original_name}' is empty",
                status_code=400,
                error_code="EMPTY_FILE",
            )

        doc_uuid = str(uuid.uuid4())
        safe_name = sanitize_filename(original_name)
        storage_path = f"documents/{doc_uuid}_{safe_name}"

        # 1. Upload to Supabase Storage
        storage_service.upload_file(
            path=storage_path,
            file_bytes=content,
            content_type="application/pdf",
        )

        # 2. Register document in Supabase PostgreSQL
        doc_record = doc_service.create_document(
            name=safe_name,
            original_name=original_name,
            size_bytes=file_size,
            storage_path=storage_path,
        )

        # 3. Dispatch background ingestion pipeline
        background_tasks.add_task(
            doc_service.process_document,
            document_id=doc_record["id"],
            file_bytes=content,
            original_name=original_name,
        )

        created_documents.append(
            DocumentResponse(
                id=doc_record["id"],
                name=doc_record["name"],
                original_name=doc_record["original_name"],
                size_bytes=doc_record["size_bytes"],
                page_count=doc_record.get("page_count"),
                chunk_count=doc_record.get("chunk_count"),
                status=doc_record["status"],
                error_msg=doc_record.get("error_msg"),
                created_at=str(doc_record["created_at"]),
                updated_at=str(doc_record["updated_at"]),
            )
        )

    return DocumentUploadResponse(
        documents=created_documents,
        message=f"Uploaded {len(created_documents)} document(s). Processing in background.",
    )


@router.get("", response_model=List[DocumentResponse])
async def list_documents():
    """Retrieve all uploaded documents and their processing status."""
    doc_service = get_document_service()
    docs = doc_service.list_documents()
    return [
        DocumentResponse(
            id=d["id"],
            name=d["name"],
            original_name=d["original_name"],
            size_bytes=d["size_bytes"],
            page_count=d.get("page_count"),
            chunk_count=d.get("chunk_count"),
            status=d["status"],
            error_msg=d.get("error_msg"),
            created_at=str(d["created_at"]),
            updated_at=str(d["updated_at"]),
        )
        for d in docs
    ]


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str = Path(..., description="Document UUID")):
    """Get metadata for a specific document."""
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)
    if not doc:
        raise AppError(f"Document {document_id} not found", status_code=404, error_code="DOCUMENT_NOT_FOUND")

    return DocumentResponse(
        id=doc["id"],
        name=doc["name"],
        original_name=doc["original_name"],
        size_bytes=doc["size_bytes"],
        page_count=doc.get("page_count"),
        chunk_count=doc.get("chunk_count"),
        status=doc["status"],
        error_msg=doc.get("error_msg"),
        created_at=str(doc["created_at"]),
        updated_at=str(doc["updated_at"]),
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str = Path(..., description="Document UUID")):
    """Lightweight endpoint for polling document ingestion status."""
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)
    if not doc:
        raise AppError(f"Document {document_id} not found", status_code=404, error_code="DOCUMENT_NOT_FOUND")

    return DocumentStatusResponse(
        id=doc["id"],
        status=doc["status"],
        page_count=doc.get("page_count"),
        chunk_count=doc.get("chunk_count"),
        error_msg=doc.get("error_msg"),
    )


@router.delete("/{document_id}")
async def delete_document(document_id: str = Path(..., description="Document UUID")):
    """Permanently delete a document from Storage, Qdrant vectors, and DB."""
    doc_service = get_document_service()
    doc_service.delete_document(document_id)
    return {"message": "Document deleted successfully", "id": document_id}


@router.get("/{document_id}/suggestions", response_model=SuggestedQuestionsResponse)
async def get_suggestions(document_id: str = Path(..., description="Document UUID")):
    """Generate 3-5 sample questions for a ready document."""
    doc_service = get_document_service()
    doc = doc_service.get_document(document_id)
    if not doc:
        raise AppError(f"Document {document_id} not found", status_code=404, error_code="DOCUMENT_NOT_FOUND")

    rag_service = get_rag_service()
    suggestions = rag_service.generate_suggestions(document_id)

    return SuggestedQuestionsResponse(
        document_id=document_id,
        document_name=doc["original_name"],
        suggestions=suggestions,
    )
