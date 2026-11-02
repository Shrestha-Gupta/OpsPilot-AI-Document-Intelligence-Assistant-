from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    name: str
    original_name: str
    size_bytes: int
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    status: str
    error_msg: Optional[str] = None
    created_at: str
    updated_at: str


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    page_count: Optional[int] = None
    chunk_count: Optional[int] = None
    error_msg: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    documents: List[DocumentResponse]
    message: str


class SuggestedQuestionsResponse(BaseModel):
    document_id: str
    document_name: str
    suggestions: List[str]
