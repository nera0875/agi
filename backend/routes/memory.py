"""
Memory API Routes - REST endpoints
Standard HTTP API for memory operations
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/memory", tags=["Memory"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class MemorySearchRequest(BaseModel):
    query: str
    limit: int = 5
    type: Optional[str] = None
    project: str = "default"


class MemoryStoreRequest(BaseModel):
    text: str
    type: str
    tags: List[str] = []
    project: str = "default"
    metadata: dict = {}


class MemorySearchResponse(BaseModel):
    results: List[dict]
    count: int
    query: str


class MemoryStoreResponse(BaseModel):
    memory_id: str
    status: str


class MemoryStatsResponse(BaseModel):
    total_memories: int
    memory_types: dict
    total_relations: int
    total_checkpoints: int
    backend: str = "PostgreSQL"
    cache: str = "Redis Stack"


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/search", response_model=MemorySearchResponse)
async def search_memory(req: MemorySearchRequest, request: Request):
    """
    Search memory using hybrid RAG

    Uses semantic search (embeddings) + BM25 full-text search
    with RRF (Reciprocal Rank Fusion) for optimal results
    """
    try:
        memory_service = request.app.state.memory_service

        results = await memory_service.hybrid_search(
            query=req.query,
            top_k=req.limit,
            user_id=req.project
        )

        return MemorySearchResponse(
            results=results,
            count=len(results),
            query=req.query
        )

    except Exception as e:
        logger.error(f"Memory search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/store", response_model=MemoryStoreResponse)
async def store_memory(req: MemoryStoreRequest, request: Request):
    """
    Store new memory with auto-embeddings

    Automatically generates embeddings using Voyage AI
    and stores in PostgreSQL with pgvector
    """
    try:
        memory_service = request.app.state.memory_service

        memory_id = await memory_service.add_memory(
            content=req.text,
            source_type=req.type,
            metadata={**req.metadata, "tags": req.tags},
            user_id=req.project
        )

        return MemoryStoreResponse(
            memory_id=str(memory_id),
            status="stored"
        )

    except Exception as e:
        logger.error(f"Memory store error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(request: Request):
    """Get memory system statistics"""
    try:
        memory_service = request.app.state.memory_service
        stats = await memory_service.get_stats()

        return MemoryStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Memory stats error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def memory_health():
    """Memory API health check"""
    return {
        "status": "healthy",
        "api": "memory",
        "endpoints": ["/search", "/store", "/stats"]
    }
