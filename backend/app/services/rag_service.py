"""
RAG Service orchestrating question answering.
Pipeline:
User question -> Gemini Query Embedding -> Qdrant Vector Retrieval -> Context Assembly -> Groq LLM -> Response with Source Citations
"""
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

from app.config import get_settings
from app.core.exceptions import AppError
from app.services.embedding_service import get_embedding_service
from app.services.vector_service import get_vector_service
from app.services.conversation_service import get_conversation_service
from app.services.document_service import get_document_service

logger = logging.getLogger("opspilot.rag")

SYSTEM_PROMPT = """You are OpsPilot, an expert AI Document Intelligence Assistant.
Your task is to provide accurate, objective, clear, and user-friendly answers strictly based on the provided document excerpts.

Grounding rules:
1. Ground every factual claim strictly in the provided Context excerpts.
2. If the context does not contain enough information to answer the question, truthfully state: "Based on the provided documents, I could not find information regarding this question." Do not extrapolate or fabricate facts.
3. Never invent document content.
4. Each excerpt includes its exact source document name and page number. Preserve that attribution. Never attribute content from one document to another.
5. When multiple documents are provided, explicitly distinguish which document supports each point. For comparisons, analyze each selected document separately before stating similarities or differences.
6. Do not claim that a document contains information unless that information appears in its supplied excerpts.

Answer formatting rules:
7. Start with a short, direct answer or overview before detailed explanation when appropriate.
8. Use clean Markdown for readability: headings, bold terms, bullet lists, numbered lists, and tables only when they genuinely improve clarity.
9. Keep paragraphs short and scannable. Avoid unnecessary repetition of the user's question.
10. For comparisons, prefer a concise Markdown table with clear column headers, followed by a short summary of the key similarities/differences.
11. Use Markdown only. Never output raw HTML tags such as <br>, <div>, <p>, or <table>.
12. Do not put Markdown table syntax inside code fences. Do not create a table when a simple bullet list is clearer.
13. Do not include source citations as fabricated links or footnotes. Source document names and page numbers are supplied separately by OpsPilot.
"""


class RAGService:
    def __init__(self):
        self.settings = get_settings()
        self.groq_client = Groq(api_key=self.settings.groq_api_key)
        self.embedding_service = get_embedding_service()
        self.vector_service = get_vector_service()
        self.conversation_service = get_conversation_service()
        self.document_service = get_document_service()

    def ask(
        self,
        conversation_id: str,
        question: str,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Execute RAG question-answering pipeline:
        1. Save user question
        2. Embed question with Gemini
        3. Search Qdrant
        4. Assemble context & conversation history
        5. Generate response with Groq LLM
        6. Save assistant message with source citations
        """
        conv = self.conversation_service.get_conversation(conversation_id)
        if not conv:
            raise AppError(
                message=f"Conversation {conversation_id} not found",
                status_code=404,
                error_code="CONVERSATION_NOT_FOUND",
            )

        self.conversation_service.add_message(
            conv_id=conversation_id,
            role="user",
            content=question,
        )

        self.conversation_service.update_title_if_default(conversation_id, question)

        query_vector = self.embedding_service.embed_query(question)

        if document_ids and len(document_ids) > 1:
            retrieved_chunks = []
            per_document_top_k = max(3, self.settings.retrieval_top_k // len(document_ids))
            for document_id in document_ids:
                doc_chunks = self.vector_service.search_chunks(
                    query_vector=query_vector,
                    top_k=per_document_top_k,
                    document_ids=[document_id],
                )
                retrieved_chunks.extend(doc_chunks)
        else:
            retrieved_chunks = self.vector_service.search_chunks(
                query_vector=query_vector,
                top_k=self.settings.retrieval_top_k,
                document_ids=document_ids,
            )

        context_parts = []
        sources: List[Dict[str, Any]] = []
        seen_sources = set()

        for idx, chunk in enumerate(retrieved_chunks):
            doc_name = chunk.get("document_name") or "Unknown Document"
            page_num = chunk.get("page_number") or 1
            chunk_text = chunk.get("chunk_text") or ""

            context_parts.append(
                f"[Excerpt {idx+1} | Source: {doc_name}, Page: {page_num}]\n{chunk_text}"
            )

            source_key = (chunk.get("document_id"), page_num)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    "document_id": chunk.get("document_id"),
                    "document_name": doc_name,
                    "page_number": page_num,
                    "chunk_text": chunk_text[:200] + "..." if len(chunk_text) > 200 else chunk_text,
                })

        context_str = (
            "\n\n".join(context_parts)
            if context_parts
            else "No relevant document excerpts found."
        )

        recent_history = self.conversation_service.get_recent_messages(
            conv_id=conversation_id,
            limit=self.settings.conversation_history_limit,
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in recent_history[:-1]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        user_prompt_with_context = (
            f"Document Context:\n"
            f"```\n{context_str}\n```\n\n"
            f"User Question: {question}"
        )
        messages.append({"role": "user", "content": user_prompt_with_context})

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.settings.groq_model,
                messages=messages,
                temperature=self.settings.groq_temperature,
                max_tokens=self.settings.groq_max_tokens,
            )
            answer = completion.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Groq completion failed: {e}")
            raise AppError(
                message=f"LLM generation failed: {str(e)}",
                status_code=500,
                error_code="LLM_GENERATION_FAILED",
            )

        saved_msg = self.conversation_service.add_message(
            conv_id=conversation_id,
            role="assistant",
            content=answer,
            sources=sources,
        )

        return {
            "message_id": saved_msg["id"],
            "conversation_id": conversation_id,
            "answer": answer,
            "sources": sources,
            "created_at": saved_msg["created_at"],
        }

    def generate_suggestions(self, document_id: str) -> List[str]:
        """Generate 3-5 suggested sample questions based on a document."""
        doc = self.document_service.get_document(document_id)
        if not doc:
            raise AppError(
                message=f"Document {document_id} not found",
                status_code=404,
                error_code="DOCUMENT_NOT_FOUND",
            )

        doc_name = doc.get("original_name", "Document")
        dummy_vector = [0.0] * self.settings.embedding_dimensions
        chunks = self.vector_service.search_chunks(
            query_vector=dummy_vector,
            top_k=3,
            document_ids=[document_id],
        )

        snippets = "\n".join([c.get("chunk_text", "")[:300] for c in chunks])

        prompt = (
            f"Document: {doc_name}\n"
            f"Sample text:\n{snippets}\n\n"
            f"Generate exactly 4 concise, diverse, high-value questions that a user might want to ask about this document. "
            f"Return ONLY the 4 questions, one per line, with no numbers, bullets, or commentary."
        )

        try:
            completion = self.groq_client.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates insightful questions."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=256,
            )
            raw_text = completion.choices[0].message.content or ""
            questions = [
                q.strip().lstrip("0123456789.- ")
                for q in raw_text.strip().split("\n")
                if q.strip()
            ]
            return questions[:5]
        except Exception as e:
            logger.error(f"Failed to generate suggestions: {e}")
            return [
                f"What is the main summary of {doc_name}?",
                "What are the key points covered in this document?",
                "Are there any specific recommendations or findings listed?",
            ]


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
