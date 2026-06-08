"""
Central configuration for the Compliance Knowledge Agent.
All settings are loaded from environment variables / .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Google Gemini ---
    gemini_api_key: str = Field(default="", description="Gemini API key")
    gemini_model: str = Field(default="gemini-1.5-flash")
    gemini_max_tokens: int = Field(default=2048)
    gemini_temperature: float = Field(default=0.1)

    # --- Embedding ---
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_device: str = Field(default="cpu")

    # --- Vector DB ---
    chroma_persist_dir: str = Field(default="./data/chroma_db")
    chroma_collection_name: str = Field(default="compliance_docs")

    # --- Reranker ---
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2")
    reranker_top_k: int = Field(default=5)

    # --- Chunking ---
    chunk_size: int = Field(default=512)
    chunk_overlap: int = Field(default=64)
    retrieval_top_k: int = Field(default=10)

    # --- API ---
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # --- Documents ---
    docs_dir: str = Field(default="./data/synthetic_docs")
    golden_set_path: str = Field(default="./data/golden_set/golden_qa_pairs.json")

    # --- Logging ---
    log_level: str = Field(default="INFO")

    @property
    def chroma_persist_path(self) -> Path:
        return Path(self.chroma_persist_dir)

    @property
    def docs_path(self) -> Path:
        return Path(self.docs_dir)

    @property
    def golden_set_file(self) -> Path:
        return Path(self.golden_set_path)


# Singleton instance
settings = Settings()
