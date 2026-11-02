"""
PDF Service for parsing and extracting page-by-page text from PDFs using PyMuPDF.
"""
import io
import logging
from typing import List, Dict, Any, Tuple
import pymupdf

from app.core.exceptions import AppError

logger = logging.getLogger("opspilot.pdf")


class PDFService:
    @staticmethod
    def validate_pdf_bytes(file_bytes: bytes, filename: str) -> None:
        """Validate PDF header, non-empty, and format."""
        if not file_bytes:
            raise AppError(
                message=f"File '{filename}' is empty.",
                status_code=400,
                error_code="EMPTY_FILE",
            )
        # Check PDF magic bytes (%PDF)
        if not file_bytes.startswith(b"%PDF"):
            raise AppError(
                message=f"File '{filename}' is not a valid PDF format (missing %PDF magic bytes).",
                status_code=400,
                error_code="INVALID_PDF_FORMAT",
            )

    @staticmethod
    def extract_text_by_pages(file_bytes: bytes, filename: str) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Extract text from each page of the PDF.
        Returns:
            (page_count, [{"page_number": int, "text": str}])
        """
        PDFService.validate_pdf_bytes(file_bytes, filename)

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as e:
            logger.error(f"Failed to open PDF '{filename}': {e}")
            raise AppError(
                message=f"Could not read PDF '{filename}'. File may be corrupt or encrypted.",
                status_code=400,
                error_code="CORRUPT_PDF",
            )

        if doc.is_encrypted:
            try:
                # Try opening without password
                if not doc.authenticate(""):
                    raise AppError(
                        message=f"PDF '{filename}' is password-protected.",
                        status_code=400,
                        error_code="ENCRYPTED_PDF",
                    )
            except Exception:
                raise AppError(
                    message=f"PDF '{filename}' is password-protected.",
                    status_code=400,
                    error_code="ENCRYPTED_PDF",
                )

        page_count = len(doc)
        if page_count == 0:
            raise AppError(
                message=f"PDF '{filename}' contains 0 pages.",
                status_code=400,
                error_code="EMPTY_PDF",
            )

        pages_data: List[Dict[str, Any]] = []
        total_text_length = 0

        for page_index in range(page_count):
            page = doc[page_index]
            text = page.get_text("text") or ""
            text = text.strip()
            total_text_length += len(text)
            pages_data.append({
                "page_number": page_index + 1,  # 1-indexed for display
                "text": text,
            })

        doc.close()

        # Check if PDF contains readable text or is likely scanned images
        if total_text_length < 20:
            logger.warning(f"PDF '{filename}' has very little text ({total_text_length} chars across {page_count} pages).")
            # We don't fail hard, but warn, and if 0 chars we raise an informative error
            if total_text_length == 0:
                raise AppError(
                    message=f"PDF '{filename}' contains no readable text. It may consist entirely of scanned images or unsupported font encodings.",
                    status_code=400,
                    error_code="NO_TEXT_FOUND",
                )

        return page_count, pages_data


_pdf_service: PDFService | None = None


def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
