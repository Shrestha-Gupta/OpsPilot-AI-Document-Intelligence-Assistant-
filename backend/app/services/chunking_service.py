"""
Chunking service for splitting document pages into overlapping text chunks.
Preserves page number provenance for precise source citations.
"""
import logging
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import get_settings

logger = logging.getLogger("opspilot.chunking")


class ChunkingService:
    def __init__(self):
        settings = get_settings()
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def chunk_pages(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split text from each page into chunks, retaining page number metadata.
        Returns:
            [
                {
                    "chunk_index": int,
                    "chunk_text": str,
                    "page_number": int,
                    "char_count": int,
                }
            ]
        """
        chunks: List[Dict[str, Any]] = []
        global_index = 0

        for page in pages:
            page_number = page["page_number"]
            page_text = page.get("text", "")

            if not page_text:
                continue

            # Split page text into chunks
            split_texts = self.splitter.split_text(page_text)
            for text in split_texts:
                cleaned = text.strip()
                if not cleaned:
                    continue

                chunks.append({
                    "chunk_index": global_index,
                    "chunk_text": cleaned,
                    "page_number": page_number,
                    "char_count": len(cleaned),
                })
                global_index += 1

        logger.info(f"Chunked {len(pages)} pages into {len(chunks)} chunks (size={self.chunk_size}, overlap={self.chunk_overlap})")
        return chunks


_chunking_service: ChunkingService | None = None


def get_chunking_service() -> ChunkingService:
    global _chunking_service
    if _chunking_service is None:
        _chunking_service = ChunkingService()
    return _chunking_service
