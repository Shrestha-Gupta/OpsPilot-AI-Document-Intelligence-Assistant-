from langchain_huggingface import HuggingFaceEmbeddings

from app.config import settings


class EmbeddingService:
    def __init__(self):
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    def get_model(self):
        return self.embedding_model