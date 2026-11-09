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
from fastapi.responses import HTMLResponse

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


@router.get("/upload-test/page", response_class=HTMLResponse, include_in_schema=False)
async def upload_test_page():
    """Temporary browser-based upload page for isolated OCR testing."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpsPilot OCR Upload Test</title>
<style>
body{font:16px system-ui;background:#111;color:#eee;max-width:760px;margin:50px auto;padding:24px}
main{border:1px solid #444;border-radius:14px;padding:28px}button{background:#d99a3d;border:0;border-radius:8px;padding:12px 20px;font-weight:700;cursor:pointer}
pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#222;padding:16px;border-radius:8px}input{margin:18px 0}
</style></head><body><main><h1>OpsPilot — OCR test</h1>
<p>Select a scanned PDF and upload it to this isolated test service.</p>
<form id="f"><input id="pdf" type="file" accept="application/pdf,.pdf" required><br><button>Upload PDF</button></form>
<h3>Result</h3><pre id="out">Waiting for PDF…</pre></main>
<script>
const form=document.getElementById('f'),out=document.getElementById('out');
form.addEventListener('submit',async e=>{
 e.preventDefault();const file=document.getElementById('pdf').files[0];if(!file)return;
 const data=new FormData();data.append('files',file);out.textContent='Uploading…';
 try{
  const res=await fetch('/api/v1/documents/upload',{method:'POST',body:data});
  const body=await res.json();if(!res.ok){out.textContent=JSON.stringify(body,null,2);return;}
  const doc=body.documents&&body.documents[0];if(!doc){out.textContent=JSON.stringify(body,null,2);return;}
  out.textContent='Uploaded. Checking processing status…\\n'+JSON.stringify(doc,null,2);
  for(let i=0;i<90;i++){
   await new Promise(r=>setTimeout(r,2000));
   const sr=await fetch('/api/v1/documents/'+doc.id+'/status');const status=await sr.json();
   out.textContent=JSON.stringify(status,null,2);
   if(status.status==='ready'||status.status==='failed')break;
  }
 }catch(err){out.textContent='Request failed: '+err.message;}
});
</script></body></html>"""


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
