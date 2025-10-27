"""
AGI-V2 Backend Configuration Settings
"""

import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "your-secret-key-change-in-production"
    
    # Database URLs
    database_url: str = "postgresql://agi_user:password@localhost:5432/agi_db"
    neo4j_url: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    redis_url: str = "redis://localhost:6379"
    
    # External API Keys
    anthropic_api_key: Optional[str] = None
    voyage_api_key: Optional[str] = None
    cohere_api_key: Optional[str] = None
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Performance
    db_pool_size: int = 20
    db_max_overflow: int = 30
    redis_max_connections: int = 50
    neo4j_max_connection_pool_size: int = 50
    
    # Memory Configuration
    memory_l1_ttl: int = 3600      # 1 hour
    memory_l2_ttl: int = 86400     # 24 hours  
    memory_l3_ttl: int = 2592000   # 30 days
    
    # JWT Configuration
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Development
    debug_mode: bool = True
    enable_swagger_ui: bool = True
    enable_redoc: bool = True
    reload: bool = True
    
    @field_validator('cors_origins', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        return []
    
    @field_validator('database_url', mode='before')
    @classmethod
    def parse_database_url(cls, v):
        if isinstance(v, str) and v.startswith("postgresql://"):
            return v
        # Fallback construction if needed
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()