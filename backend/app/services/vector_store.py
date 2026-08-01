from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import VECTOR_DB_DIR
from app.services.embeddings import EmbeddingService


class VectorStoreService:

    def __init__(self):
        self.embedding_model = EmbeddingService().get_model()

    def create_vector_store(self, chunks):

        documents = []

        for chunk in chunks:
            documents.append(
                Document(
                    page_content=chunk["text"],
                    metadata={
                        "document": chunk["document"],
                        "page": chunk["page"],
                    },
                )
            )

        if not documents:
            raise ValueError("No chunks available to create vector store.")

        vector_store = FAISS.from_documents(
            documents,
            self.embedding_model,
        )

        vector_store.save_local(str(VECTOR_DB_DIR))

        return vector_store

    def load_vector_store(self):

        return FAISS.load_local(
            str(VECTOR_DB_DIR),
            self.embedding_model,
            allow_dangerous_deserialization=True,
        )

    def get_retriever(self):

        vector_store = self.load_vector_store()

        return vector_store.as_retriever(
            search_kwargs={"k": 4}
        )