"""
Application configuration management
Uses pydantic-settings for environment variable validation
"""

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
import os

# Get backend directory absolute path
BACKEND_DIR = Path(__file__).parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings with environment variable loading"""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ========================================================================
    # APPLICATION
    # ========================================================================
    environment: str = Field(default="production", description="Environment")
    log_level: str = Field(default="info", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")

    # ========================================================================
    # DATABASE
    # ========================================================================
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL"
    )

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql://"):
            raise ValueError("DATABASE_URL must start with postgresql://")
        return v

    # ========================================================================
    # REDIS
    # ========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379",
        description="Redis connection URL"
    )

    # ========================================================================
    # LANGCHAIN / LANGSMITH
    # ========================================================================
    langchain_tracing_v2: str = Field(
        default="true",
        description="Enable LangSmith tracing"
    )
    langchain_api_key: str = Field(
        ...,
        description="LangSmith API key"
    )
    langchain_project: str = Field(
        default="agi-production",
        description="LangSmith project name"
    )
    langchain_endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith endpoint"
    )

    # ========================================================================
    # LLM PROVIDERS
    # ========================================================================
    anthropic_api_key: str = Field(
        ...,
        description="Anthropic Claude API key"
    )

    # ========================================================================
    # EMBEDDINGS
    # ========================================================================
    voyage_api_key: str = Field(
        ...,
        description="Voyage AI API key for embeddings"
    )
    voyage_model: str = Field(
        default="voyage-3",
        description="Voyage embedding model"
    )

    # ========================================================================
    # RERANKING
    # ========================================================================
    cohere_api_key: str = Field(
        ...,
        description="Cohere API key for reranking"
    )

    # ========================================================================
    # ERROR TRACKING
    # ========================================================================
    sentry_dsn: Optional[str] = Field(
        default=None,
        description="Sentry DSN for error tracking"
    )
    sentry_environment: str = Field(
        default="production",
        description="Sentry environment tag"
    )

    # ========================================================================
    # SECURITY
    # ========================================================================
    jwt_secret: str = Field(
        ...,
        description="JWT signing secret"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    jwt_expiration_minutes: int = Field(
        default=60,
        description="JWT expiration time in minutes"
    )
    admin_username: str = Field(
        default="demo",
        description="Default administrator username (override in production)"
    )
    admin_password_hash: str = Field(
        default="$2b$12$PETUM4Su2f..s3qxvZZdUetRbdv8sIn2t7z5VyW8NPTG/Q3twf6w.",
        description="BCrypt hash for the administrator password"
    )

    # ========================================================================
    # RATE LIMITING
    # ========================================================================
    rate_limit_per_minute: int = Field(
        default=100,
        description="Rate limit per minute per user"
    )
    rate_limit_per_hour: int = Field(
        default=1000,
        description="Rate limit per hour per user"
    )

    # ========================================================================
    # RAG CONFIGURATION
    # ========================================================================
    chunk_size: int = Field(
        default=512,
        description="Text chunk size for semantic splitting"
    )
    chunk_overlap: int = Field(
        default=100,
        description="Overlap between chunks"
    )
    top_k_retrieval: int = Field(
        default=10,
        description="Number of documents to retrieve"
    )
    semantic_weight: float = Field(
        default=0.7,
        description="Weight for semantic search in RRF"
    )
    bm25_weight: float = Field(
        default=0.3,
        description="Weight for BM25 search in RRF"
    )
    rerank_top_n: int = Field(
        default=5,
        description="Number of documents after reranking"
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


# Global settings instance
settings = Settings()
