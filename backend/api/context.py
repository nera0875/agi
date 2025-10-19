"""
GraphQL Context - Dependency injection for Strawberry
"""

from typing import Optional
from strawberry.fastapi import BaseContext
from starlette.requests import Request
from starlette.responses import Response


class Context(BaseContext):
    """Custom GraphQL context with dependency injection"""

    def __init__(self):
        super().__init__()
        self.request = None
        self.response = None
        self.memory_service = None
        self.agent_service = None
        self.graph_service = None
        self.db_pool = None
        self.redis_client = None
        self.user_id = None


async def get_context(
    request: Request,
    response: Response
) -> Context:
    """
    Context factory for Strawberry FastAPI

    Args:
        request: FastAPI request object
        response: FastAPI response object

    Returns:
        GraphQL context with injected services
    """
    context = Context()

    # Add request and response to context
    context.request = request
    context.response = response

    # Add services from app state
    if hasattr(request.app, "state"):
        if hasattr(request.app.state, "memory_service"):
            context.memory_service = request.app.state.memory_service
        if hasattr(request.app.state, "agent_service"):
            context.agent_service = request.app.state.agent_service
        if hasattr(request.app.state, "db_pool"):
            context.db_pool = request.app.state.db_pool
        if hasattr(request.app.state, "redis_client"):
            context.redis_client = request.app.state.redis_client
        if hasattr(request.app.state, "graph_service"):
            context.graph_service = request.app.state.graph_service

    # Extract JWT token if present
    try:
        import jwt
        from config import settings

        token = request.headers.get("Authorization", "").replace("Bearer ", "")
        if token:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            context.user_id = payload.get("sub")
    except Exception:
        pass

    return context
