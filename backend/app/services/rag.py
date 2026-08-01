from langchain_core.prompts import ChatPromptTemplate

from app.services.chunking import TextChunker
from app.services.llm import LLMService
from app.services.pdf_loader import PDFLoader
from app.services.vector_store import VectorStoreService


class RAGService:

    def __init__(self):
        self.chunker = TextChunker()
        self.vector_store = VectorStoreService()
        self.llm = LLMService().get_llm()

    def index_documents(self, pdf_paths):

        all_chunks = []

        for pdf_path in pdf_paths:

            pages = PDFLoader.extract_text(pdf_path)

            chunks = self.chunker.chunk_document(
                pdf_path.name,
                pages,
            )

            all_chunks.extend(chunks)

        if not all_chunks:
            raise ValueError(
                "No text could be extracted from uploaded documents."
            )

        self.vector_store.create_vector_store(all_chunks)

        return len(all_chunks)

    def ask(self, question: str):

        retriever = self.vector_store.get_retriever()

        docs = retriever.invoke(question)

        if not docs:
            return {
                "answer": "I couldn't find any relevant information in the uploaded documents.",
                "sources": [],
            }

        context = "\n\n".join(
            doc.page_content for doc in docs
        )

        prompt = ChatPromptTemplate.from_template(
            """
You are OpsPilot, an AI Document Intelligence Assistant.

Your task is to answer questions ONLY using the provided context.

Rules:
- Do NOT make up information.
- If the answer is not available in the context, reply exactly:
  "I couldn't find this information in the uploaded documents."
- Keep answers clear, concise, and well-structured.
- If multiple documents contain relevant information, combine it into one response.

Context:
{context}

Question:
{question}
"""
        )

        messages = prompt.format_messages(
            context=context,
            question=question,
        )

        try:
            response = self.llm.invoke(messages)

            # Remove duplicate sources
            seen = set()
            unique_sources = []

            for doc in docs:
                source = (
                    doc.metadata["document"],
                    doc.metadata["page"],
                )

                if source not in seen:
                    seen.add(source)
                    unique_sources.append(
                        {
                            "document": doc.metadata["document"],
                            "page": doc.metadata["page"],
                        }
                    )

            return {
                "answer": response.content,
                "sources": unique_sources,
            }

        except Exception as e:
            print(f"LLM Error: {e}")

            return {
                "answer": "Sorry, the AI service is temporarily unavailable. Please try again later.",
                "sources": [],
            }