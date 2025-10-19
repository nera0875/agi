#!/usr/bin/env python3
"""
AGI Memory System - Configuration Manager

Centralizes all configuration for the AGI memory system.
Loads from .env file and provides typed access to settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AGIConfig(BaseSettings):
    """
    Unified configuration for AGI Memory System

    Providers: OpenAI, Anthropic, Cohere, Voyage AI
    Infrastructure: PostgreSQL, Redis, Neo4j
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ═══════════════════════════════════════════════════════
    # AI PROVIDERS
    # ═══════════════════════════════════════════════════════

    # OpenAI
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_organization: Optional[str] = Field(None, description="OpenAI organization ID")

    # Anthropic Claude
    anthropic_api_key: str = Field(..., description="Anthropic API key")

    # Cohere
    cohere_api_key: str = Field(..., description="Cohere API key")

    # Voyage AI
    voyage_api_key: str = Field(..., description="Voyage AI API key")

    # ═══════════════════════════════════════════════════════
    # LANGCHAIN / LANGSMITH
    # ═══════════════════════════════════════════════════════

    langsmith_api_key: Optional[str] = Field(None, description="LangSmith API key")
    langsmith_project: str = Field("agi-memory-system", description="LangSmith project name")
    langsmith_tracing: bool = Field(True, description="Enable LangSmith tracing")

    # ═══════════════════════════════════════════════════════
    # DATABASES
    # ═══════════════════════════════════════════════════════

    # PostgreSQL
    postgres_host: str = Field("localhost", description="PostgreSQL host")
    postgres_port: int = Field(5432, description="PostgreSQL port")
    postgres_db: str = Field("agi_db", description="PostgreSQL database name")
    postgres_user: str = Field("agi_user", description="PostgreSQL user")
    postgres_password: str = Field("agi_password", description="PostgreSQL password")

    # Redis
    redis_host: str = Field("localhost", description="Redis host")
    redis_port: int = Field(6379, description="Redis port")
    redis_db: int = Field(0, description="Redis database number")
    redis_password: Optional[str] = Field(None, description="Redis password")

    # Neo4j
    neo4j_uri: str = Field("bolt://localhost:7687", description="Neo4j connection URI")
    neo4j_user: str = Field("neo4j", description="Neo4j username")
    neo4j_password: str = Field("Voiture789", description="Neo4j password")

    # ═══════════════════════════════════════════════════════
    # SYSTEM
    # ═══════════════════════════════════════════════════════

    environment: str = Field("development", description="Environment (development/production)")
    log_level: str = Field("INFO", description="Logging level")
    max_concurrent_requests: int = Field(10, description="Max concurrent API requests")
    request_timeout: int = Field(30, description="Request timeout in seconds")
    enable_cost_tracking: bool = Field(True, description="Enable cost tracking")

    # ═══════════════════════════════════════════════════════
    # COMPUTED PROPERTIES
    # ═══════════════════════════════════════════════════════

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL"""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    def setup_langsmith(self):
        """Setup LangSmith environment variables for tracing"""
        if self.langsmith_api_key and self.langsmith_tracing:
            os.environ["LANGSMITH_API_KEY"] = self.langsmith_api_key
            os.environ["LANGSMITH_PROJECT"] = self.langsmith_project
            os.environ["LANGSMITH_TRACING"] = "true"
            return True
        return False


# Singleton instance
_config: Optional[AGIConfig] = None

def get_config() -> AGIConfig:
    """Get or create AGI configuration singleton"""
    global _config
    if _config is None:
        # Try to load from .env file in project root
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            _config = AGIConfig(_env_file=str(env_path))
        else:
            # Fallback to .env.agi-memory template
            env_path = Path(__file__).parent.parent.parent / ".env.agi-memory"
            if env_path.exists():
                print(f"⚠️  Using template .env.agi-memory - Please copy to .env and configure!")
                _config = AGIConfig(_env_file=str(env_path))
            else:
                # Use environment variables only
                _config = AGIConfig()

    return _config


# Export convenience function
def init_config() -> AGIConfig:
    """Initialize and return configuration"""
    config = get_config()
    config.setup_langsmith()
    return config


if __name__ == "__main__":
    # Test configuration
    config = init_config()
    print("✅ AGI Configuration loaded:")
    print(f"  - PostgreSQL: {config.postgres_url}")
    print(f"  - Redis: {config.redis_url}")
    print(f"  - Neo4j: {config.neo4j_uri}")
    print(f"  - Environment: {config.environment}")
    print(f"  - LangSmith: {'Enabled' if config.langsmith_tracing else 'Disabled'}")
