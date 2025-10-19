"""
AGI System - FastAPI Application
Main entry point with GraphQL integration
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from strawberry.fastapi import GraphQLRouter

from config import settings
from services.database import db
from services.redis_client import redis_client
from services.memory_service import MemoryService
from services.agent_service import AgentService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Sentry (if configured)
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=1.0 if settings.is_development else 0.1,
        profiles_sample_rate=1.0 if settings.is_development else 0.1,
    )
    logger.info("Sentry initialized")


# Global service instances
memory_service: Optional[MemoryService] = None
agent_service: Optional[AgentService] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    global memory_service, agent_service
    
    # Startup
    logger.info("Starting AGI System backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"LangSmith Project: {settings.langchain_project}")

    try:
        # Initialize database connection pool
        db_pool = await db.connect()
        logger.info("Database connection pool initialized")

        # Initialize Redis connection
        redis_conn = await redis_client.connect()
        logger.info("Redis connection established")

        # Initialize memory service
        memory_service = MemoryService(db_pool, redis_conn)
        logger.info("Memory service initialized")

        # Initialize agent service
        agent_service = AgentService(db_pool, memory_service)
        logger.info("Agent service initialized")

        # Make services available to context
        app.state.memory_service = memory_service
        app.state.agent_service = agent_service
        app.state.db_pool = db_pool
        app.state.redis_client = redis_conn

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down AGI System backend...")
    try:
        await redis_client.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis: {e}")

    try:
        await db.disconnect()
        logger.info("Database connection pool closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")


# Create FastAPI application
app = FastAPI(
    title="AGI System API",
    description="Production-ready AGI system with LangChain/LangGraph",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (Vercel + local)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/K8s"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AGI System API",
        "version": "0.1.0",
        "docs": "/docs",
        "graphql": "/graphql"
    }


# ============================================================================
# GRAPHQL INTEGRATION
# ============================================================================

from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from api import schema, get_context

# Create GraphQL router with WebSocket support and debug mode
graphql_app = GraphQLRouter(
    schema,
    context_getter=get_context,
    subscription_protocols=[
        GRAPHQL_TRANSPORT_WS_PROTOCOL,
        GRAPHQL_WS_PROTOCOL
    ],
    graphql_ide="apollo-sandbox" if settings.is_development else None
)

# Mount GraphQL endpoint
app.include_router(graphql_app, prefix="/graphql")

# Mount REST API routes
from routes import memory_router, mcp_router
app.include_router(memory_router)
app.include_router(mcp_router)

# Mount static files (dashboard)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dashboard route
@app.get("/dashboard")
async def dashboard():
    """Serve management dashboard"""
    return FileResponse("static/dashboard.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development
    )
