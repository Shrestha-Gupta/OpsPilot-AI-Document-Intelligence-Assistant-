from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings


class TextChunker:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

    def chunk_document(self, document_name: str, pages: list):
        chunks = []

        for page in pages:

            # Skip empty pages
            if not page["text"].strip():
                continue

            split_chunks = self.splitter.split_text(page["text"])

            for chunk in split_chunks:
                chunks.append(
                    {
                        "document": document_name,
                        "page": page["page"],
                        "text": chunk,
                    }
                )

        return chunks