from fastapi import APIRouter

from app.schemas.chat import ChatRequest
from app.services.rag import RAGService

router = APIRouter(tags=["Chat"])


@router.post("/chat")
async def chat(request: ChatRequest):
    rag_service = RAGService()
    return rag_service.ask(question=request.question)


@router.get("/chat")
def chat_status():
    return {"message": "Chat route is ready"}