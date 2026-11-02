"""
Conversation and Chat API endpoints:
- List conversations
- Create new conversation
- Get conversation with full message history
- Delete conversation
- Clear conversation messages
- Send chat message (RAG execution)
"""
import logging
from typing import List, Optional
from fastapi import APIRouter, Path

from app.schemas.chat import (
    ConversationResponse,
    ConversationDetailResponse,
    CreateConversationRequest,
    ChatRequest,
    ChatResponse,
    MessageResponse,
    SourceCitation,
)
from app.services.conversation_service import get_conversation_service
from app.services.rag_service import get_rag_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])
logger = logging.getLogger("opspilot.api.conversations")


@router.get("", response_model=List[ConversationResponse])
async def list_conversations():
    """List all conversation threads."""
    conv_service = get_conversation_service()
    threads = conv_service.list_conversations()
    return [
        ConversationResponse(
            id=t["id"],
            title=t.get("title"),
            created_at=str(t["created_at"]),
            updated_at=str(t["updated_at"]),
        )
        for t in threads
    ]


@router.post("", response_model=ConversationResponse)
async def create_conversation(payload: Optional[CreateConversationRequest] = None):
    """Create a new conversation session."""
    conv_service = get_conversation_service()
    title = payload.title if payload else None
    new_conv = conv_service.create_conversation(title=title)
    return ConversationResponse(
        id=new_conv["id"],
        title=new_conv.get("title"),
        created_at=str(new_conv["created_at"]),
        updated_at=str(new_conv["updated_at"]),
    )


@router.get("/{conv_id}", response_model=ConversationDetailResponse)
async def get_conversation(conv_id: str = Path(..., description="Conversation UUID")):
    """Get conversation details and full message history."""
    conv_service = get_conversation_service()
    conv = conv_service.get_conversation_with_messages(conv_id)

    formatted_messages = []
    for m in conv.get("messages", []):
        raw_sources = m.get("sources") or []
        parsed_sources = [
            SourceCitation(
                document_id=s.get("document_id", ""),
                document_name=s.get("document_name", ""),
                page_number=s.get("page_number", 1),
                chunk_text=s.get("chunk_text"),
            )
            for s in raw_sources
        ] if raw_sources else None

        formatted_messages.append(
            MessageResponse(
                id=m["id"],
                conversation_id=m["conversation_id"],
                role=m["role"],
                content=m["content"],
                sources=parsed_sources,
                created_at=str(m["created_at"]),
            )
        )

    return ConversationDetailResponse(
        id=conv["id"],
        title=conv.get("title"),
        created_at=str(conv["created_at"]),
        updated_at=str(conv["updated_at"]),
        messages=formatted_messages,
    )


@router.delete("/{conv_id}")
async def delete_conversation(conv_id: str = Path(..., description="Conversation UUID")):
    """Permanently delete a conversation thread and all messages."""
    conv_service = get_conversation_service()
    conv_service.delete_conversation(conv_id)
    return {"message": "Conversation deleted successfully", "id": conv_id}


@router.post("/{conv_id}/clear")
async def clear_conversation_messages(conv_id: str = Path(..., description="Conversation UUID")):
    """Clear all messages from a conversation thread."""
    conv_service = get_conversation_service()
    conv_service.clear_messages(conv_id)
    return {"message": "Messages cleared successfully", "id": conv_id}


@router.post("/{conv_id}/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    conv_id: str = Path(..., description="Conversation UUID"),
):
    """
    Send question to RAG pipeline:
    - Embeds question with Gemini
    - Retrieves relevant chunks from Qdrant
    - Generates grounded answer using Groq LLM
    - Returns answer with source citations
    """
    rag_service = get_rag_service()
    res = rag_service.ask(
        conversation_id=conv_id,
        question=payload.question,
        document_ids=payload.document_ids,
    )

    return ChatResponse(
        message_id=res["message_id"],
        conversation_id=res["conversation_id"],
        answer=res["answer"],
        sources=[
            SourceCitation(
                document_id=s["document_id"],
                document_name=s["document_name"],
                page_number=s["page_number"],
                chunk_text=s.get("chunk_text"),
            )
            for s in res.get("sources", [])
        ],
        created_at=str(res["created_at"]),
    )
