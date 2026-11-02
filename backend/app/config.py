# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    log_level: str = "INFO"

    # CORS
    frontend_url: str = "http://localhost:5173"

    # Supabase
    supabase_url: str
    supabase_service_key: str
    supabase_bucket_name: str = "pdfs"

    # Qdrant
    qdrant_url: str
    qdrant_api_key: str
    qdrant_collection_name: str = "opspilot_chunks"

    # Gemini Embeddings
    gemini_api_key: str
    embedding_model: str = "gemini-embedding-001"
    embedding_dimensions: int = 768
    embedding_batch_size: int = 20

    # Groq
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    groq_max_tokens: int = 1024
    groq_temperature: float = 0.1

    # Upload limits
    max_file_size_mb: int = 20
    max_files_per_upload: int = 5

    # RAG
    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_top_k: int = 5
    conversation_history_limit: int = 10

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
