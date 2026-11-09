"""
PDF Service for page-wise text extraction with OCR fallback for scanned pages.
"""
import io
import logging
import os
from typing import List, Dict, Any, Tuple

import pymupdf
from PIL import Image
import pytesseract
from pytesseract import TesseractNotFoundError

from app.core.exceptions import AppError

logger = logging.getLogger("opspilot.pdf")

OCR_LANG = os.getenv("OPSPILOT_OCR_LANG", "eng")
OCR_DPI_SCALE = float(os.getenv("OPSPILOT_OCR_DPI_SCALE", "2.0"))
MIN_PAGE_TEXT_LENGTH = 20


class PDFService:
    @staticmethod
    def validate_pdf_bytes(file_bytes: bytes, filename: str) -> None:
        """Validate PDF header and non-empty content."""
        if not file_bytes:
            raise AppError(
                message=f"File '{filename}' is empty.",
                status_code=400,
                error_code="EMPTY_FILE",
            )
        if not file_bytes.startswith(b"%PDF"):
            raise AppError(
                message=f"File '{filename}' is not a valid PDF format (missing %PDF magic bytes).",
                status_code=400,
                error_code="INVALID_PDF_FORMAT",
            )

    @staticmethod
    def _ocr_page(page: pymupdf.Page, filename: str, page_number: int) -> str:
        """Render one PDF page and recognize its text using the local Tesseract engine."""
        try:
            ocr_started = __import__("time").perf_counter()
            pix = page.get_pixmap(
                matrix=pymupdf.Matrix(OCR_DPI_SCALE, OCR_DPI_SCALE),
                colorspace=pymupdf.csGRAY,
                alpha=False,
            )
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(
                image,
                lang=OCR_LANG,
                config="--oem 1 --psm 6",
            ).strip()
            logger.info(
                "OCR completed for %s page %d | duration=%.2fs | extracted_chars=%d | language=%s",
                filename,
                page_number,
                __import__("time").perf_counter() - ocr_started,
                len(text),
                OCR_LANG,
            )
            return text
        except TesseractNotFoundError as exc:
            logger.exception("Tesseract executable is unavailable")
            raise AppError(
                message="OCR engine is not installed on the server. Please contact the administrator.",
                status_code=503,
                error_code="OCR_ENGINE_UNAVAILABLE",
            ) from exc
        except Exception as exc:
            logger.exception("OCR failed for %s page %d", filename, page_number)
            raise AppError(
                message=f"OCR could not process page {page_number} of '{filename}'.",
                status_code=422,
                error_code="OCR_PROCESSING_FAILED",
            ) from exc

    @staticmethod
    def extract_text_by_pages(file_bytes: bytes, filename: str) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Extract page-by-page text. Pages without usable embedded text are OCR-processed.
        Returns (page_count, [{"page_number": int, "text": str}]).
        """
        PDFService.validate_pdf_bytes(file_bytes, filename)

        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            logger.exception("Failed to open PDF '%s'", filename)
            raise AppError(
                message=f"Could not read PDF '{filename}'. File may be corrupt or encrypted.",
                status_code=400,
                error_code="CORRUPT_PDF",
            ) from exc

        try:
            if doc.is_encrypted and not doc.authenticate(""):
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
            ocr_page_count = 0

            for page_index in range(page_count):
                page = doc[page_index]
                page_number = page_index + 1
                text = (page.get_text("text") or "").strip()

                # Run OCR only for pages where embedded text is absent or unusably sparse.
                if len(text) < MIN_PAGE_TEXT_LENGTH:
                    ocr_text = PDFService._ocr_page(page, filename, page_number)
                    if len(ocr_text) > len(text):
                        text = ocr_text
                    if ocr_text:
                        ocr_page_count += 1

                total_text_length += len(text)
                pages_data.append({
                    "page_number": page_number,
                    "text": text,
                })

            logger.info(
                "PDF extraction complete for %s | pages=%d | OCR_pages=%d | extracted_chars=%d",
                filename,
                page_count,
                ocr_page_count,
                total_text_length,
            )

            if total_text_length < MIN_PAGE_TEXT_LENGTH:
                raise AppError(
                    message=(
                        f"PDF '{filename}' contains no usable readable text, even after OCR. "
                        "It may be blank, very low quality, or use an unsupported language."
                    ),
                    status_code=400,
                    error_code="NO_TEXT_FOUND",
                )

            return page_count, pages_data
        finally:
            doc.close()


_pdf_service: PDFService | None = None


def get_pdf_service() -> PDFService:
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service
