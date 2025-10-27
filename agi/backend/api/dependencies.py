"""
AGI-V2 Backend API Dependencies
FastAPI dependency injection for services
"""

from typing import Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timezone

from config.settings import get_settings
from services.external_services import ExternalServicesManager
from services.memory_service import MemoryService
from services.graph_service import GraphService
from services.embedding_service import EmbeddingService

# Security
security = HTTPBearer()
settings = get_settings()


# Service Dependencies
def get_external_services(request: Request) -> ExternalServicesManager:
    """Get external services manager from app state"""
    if not hasattr(request.app.state, 'external_services'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="External services not initialized"
        )
    return request.app.state.external_services


def get_memory_service(request: Request) -> MemoryService:
    """Get memory service from app state"""
    if not hasattr(request.app.state, 'memory_service'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Memory service not initialized"
        )
    return request.app.state.memory_service


def get_graph_service(request: Request) -> GraphService:
    """Get graph service from app state"""
    if not hasattr(request.app.state, 'graph_service'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Graph service not initialized"
        )
    return request.app.state.graph_service


def get_embedding_service(request: Request) -> EmbeddingService:
    """Get embedding service from app state"""
    if not hasattr(request.app.state, 'embedding_service'):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding service not initialized"
        )
    return request.app.state.embedding_service


# Authentication Dependencies
async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """Extract and validate user ID from JWT token"""
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing expiration"
            )
        
        if datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user ID"
            )
        
        return user_id
        
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


async def get_optional_user_id(
    request: Request
) -> str | None:
    """Extract user ID from JWT token if present, otherwise return None"""
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        
        token = auth_header.split(" ")[1]
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            return None
        
        return payload.get("sub")
        
    except (jwt.InvalidTokenError, IndexError):
        return None


# Type aliases for dependency injection
ExternalServicesDep = Annotated[ExternalServicesManager, Depends(get_external_services)]
MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
GraphServiceDep = Annotated[GraphService, Depends(get_graph_service)]
EmbeddingServiceDep = Annotated[EmbeddingService, Depends(get_embedding_service)]
CurrentUserDep = Annotated[str, Depends(get_current_user_id)]
OptionalUserDep = Annotated[str | None, Depends(get_optional_user_id)]