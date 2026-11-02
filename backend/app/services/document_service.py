"""
Document service managing database records, status transitions,
and the document ingestion pipeline (extract -> chunk -> embed -> index).
"""
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.db.supabase import get_supabase
from app.core.exceptions import AppError
from app.services.storage_service import get_storage_service
from app.services.pdf_service import get_pdf_service
from app.services.chunking_service import get_chunking_service
from app.services.embedding_service import get_embedding_service
from app.services.vector_service import get_vector_service

logger = logging.getLogger("opspilot.document")


class DocumentService:
    def __init__(self):
        pass

    def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents ordered by created_at descending."""
        supabase = get_supabase()
        try:
            res = (
                supabase.table("documents")
                .select("*")
                .order("created_at", desc=True)
                .execute()
            )
            return res.data or []
        except Exception as e:
            logger.error(f"Failed to list documents: {e}")
            raise AppError(
                message="Failed to retrieve documents from database",
                status_code=500,
                error_code="DB_QUERY_FAILED",
            )

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single document by ID."""
        supabase = get_supabase()
        try:
            res = (
                supabase.table("documents")
                .select("*")
                .eq("id", document_id)
                .limit(1)
                .execute()
            )
            return res.data[0] if res.data else None
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise AppError(
                message=f"Failed to retrieve document: {str(e)}",
                status_code=500,
                error_code="DB_QUERY_FAILED",
            )

    def create_document(
        self,
        name: str,
        original_name: str,
        size_bytes: int,
        storage_path: str,
    ) -> Dict[str, Any]:
        """Insert a new document record with status 'processing'."""
        supabase = get_supabase()
        try:
            res = (
                supabase.table("documents")
                .insert({
                    "name": name,
                    "original_name": original_name,
                    "size_bytes": size_bytes,
                    "storage_path": storage_path,
                    "status": "processing",
                })
                .execute()
            )
            if not res.data:
                raise RuntimeError("No data returned from document insert")
            logger.info(f"Created document record: {res.data[0]['id']} ({original_name})")
            return res.data[0]
        except Exception as e:
            logger.error(f"Failed to create document record: {e}")
            raise AppError(
                message=f"Failed to save document record: {str(e)}",
                status_code=500,
                error_code="DB_INSERT_FAILED",
            )

    def update_status(
        self,
        document_id: str,
        status: str,
        page_count: Optional[int] = None,
        chunk_count: Optional[int] = None,
        error_msg: Optional[str] = None,
    ) -> None:
        """Update processing status and counts of a document."""
        supabase = get_supabase()
        payload: Dict[str, Any] = {"status": status}
        if page_count is not None:
            payload["page_count"] = page_count
        if chunk_count is not None:
            payload["chunk_count"] = chunk_count
        if error_msg is not None:
            payload["error_msg"] = error_msg

        try:
            supabase.table("documents").update(payload).eq("id", document_id).execute()
            logger.info(f"Updated document {document_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update document status for {document_id}: {e}")

    def delete_document(self, document_id: str) -> None:
        """
        Delete document across all 3 stores:
        1. Supabase Storage (PDF file)
        2. Qdrant (vector chunks)
        3. Supabase PostgreSQL (metadata row)
        """
        doc = self.get_document(document_id)
        if not doc:
            raise AppError(
                message=f"Document with ID {document_id} not found",
                status_code=404,
                error_code="DOCUMENT_NOT_FOUND",
            )

        storage_service = get_storage_service()
        vector_service = get_vector_service()
        supabase = get_supabase()

        # 1. Remove from Storage
        if doc.get("storage_path"):
            storage_service.delete_file(doc["storage_path"])

        # 2. Remove from Qdrant
        vector_service.delete_document_chunks(document_id)

        # 3. Remove from PostgreSQL
        try:
            supabase.table("documents").delete().eq("id", document_id).execute()
            logger.info(f"Successfully deleted document {document_id}")
        except Exception as e:
            logger.error(f"Failed to delete document from database: {e}")
            raise AppError(
                message=f"Failed to delete document: {str(e)}",
                status_code=500,
                error_code="DB_DELETE_FAILED",
            )

    def process_document(self, document_id: str, file_bytes: bytes, original_name: str) -> None:
        """
        Full background ingestion pipeline:
        PDF extraction -> Chunking -> Gemini Embeddings -> Qdrant Indexing.
        Updates document status throughout and tracks detailed structured timing logs.
        """
        pdf_service = get_pdf_service()
        chunking_service = get_chunking_service()
        embedding_service = get_embedding_service()
        vector_service = get_vector_service()

        t_pipeline_start = time.perf_counter()
        try:
            logger.info(f"Starting processing pipeline for document {document_id} ({original_name})")

            # 1. Extract text page-by-page
            t0 = time.perf_counter()
            page_count, pages = pdf_service.extract_text_by_pages(file_bytes, original_name)
            t_extract = time.perf_counter() - t0
            logger.info(f"Extracted {page_count} pages from {original_name} in {t_extract:.3f}s")

            # 2. Split pages into chunks
            t0 = time.perf_counter()
            chunks = chunking_service.chunk_pages(pages)
            t_chunk = time.perf_counter() - t0
            if not chunks:
                raise AppError(
                    message=f"No text chunks could be extracted from '{original_name}'",
                    status_code=400,
                    error_code="EMPTY_CHUNKS",
                )
            logger.info(f"Created {len(chunks)} chunks in {t_chunk:.3f}s")

            # Early metadata update: expose page_count and chunk_count to polling frontend while processing
            self.update_status(
                document_id=document_id,
                status="processing",
                page_count=page_count,
                chunk_count=len(chunks),
            )

            # 3. Generate Gemini embeddings
            t0 = time.perf_counter()
            chunk_texts = [c["chunk_text"] for c in chunks]
            embeddings = embedding_service.embed_documents(
                texts=chunk_texts,
                title=original_name,
            )
            t_embed = time.perf_counter() - t0
            logger.info(f"Generated {len(embeddings)} embeddings in {t_embed:.3f}s")

            # 4. Upsert into Qdrant
            t0 = time.perf_counter()
            vector_service.upsert_chunks(
                document_id=document_id,
                document_name=original_name,
                chunks=chunks,
                embeddings=embeddings,
            )
            t_index = time.perf_counter() - t0
            logger.info(f"Indexed {len(chunks)} vectors in Qdrant in {t_index:.3f}s")

            # 5. Mark ready
            t_total = time.perf_counter() - t_pipeline_start
            self.update_status(
                document_id=document_id,
                status="ready",
                page_count=page_count,
                chunk_count=len(chunks),
            )
            logger.info(
                "[Pipeline Complete] Document %s (%s): "
                "PDF extraction: %.2fs | Chunking: %.2fs | Embeddings: %.2fs | Qdrant indexing: %.2fs | Total: %.2fs",
                document_id, original_name, t_extract, t_chunk, t_embed, t_index, t_total,
            )

        except Exception as e:
            t_failed = time.perf_counter() - t_pipeline_start
            error_message = str(e)
            logger.exception(
                "Pipeline failed for document %s after %.2fs: %s",
                document_id,
                t_failed,
                error_message,
            )
            try:
                self.update_status(
                    document_id=document_id,
                    status="failed",
                    error_msg=error_message,
                )
            except Exception:
                logger.exception(
                    "Failed to persist failed status for document %s",
                    document_id,
                )


_document_service: DocumentService | None = None


def get_document_service() -> DocumentService:
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
