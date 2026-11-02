from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    document_id: str
    document_name: str
    page_number: int
    chunk_text: Optional[str] = None


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="User question")
    document_ids: Optional[List[str]] = Field(default=None, description="Optional scope of documents")


class ChatResponse(BaseModel):
    message_id: str
    conversation_id: str
    answer: str
    sources: List[SourceCitation] = []
    created_at: str


class CreateConversationRequest(BaseModel):
    title: Optional[str] = None


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role: str
    content: str
    sources: Optional[List[SourceCitation]] = None
    created_at: str


class ConversationResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: str
    updated_at: str


class ConversationDetailResponse(ConversationResponse):
    messages: List[MessageResponse] = []
