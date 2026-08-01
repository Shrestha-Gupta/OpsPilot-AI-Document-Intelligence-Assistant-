from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Backend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Folders
UPLOAD_DIR = BASE_DIR / "uploads"
VECTOR_DB_DIR = BASE_DIR / "vector_db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    # RAG Settings
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Embedding Model
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Groq
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"


settings = Settings()

# Create required folders
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)