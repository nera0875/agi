"""
Routes de gestion des mémoires pour l'API AGI
Gestion des mémoires L1/L2/L3, recherche sémantique et consolidation
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from backend.api.dependencies import (
    MemoryServiceDep,
    EmbeddingServiceDep,
    CurrentUserDep,
    OptionalUserDep
)
from backend.services.memory_service import MemoryLevel

router = APIRouter(prefix="/memory", tags=["memory"])

# Modèles Pydantic pour les requêtes/réponses
class MemoryCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)
    level: str = Field(default=MemoryLevel.L1, regex="^(L1|L2|L3)$")
    importance: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: Optional[str] = None

class MemoryResponse(BaseModel):
    id: str
    user_id: str
    content: str
    level: str
    importance: float
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    conversation_id: Optional[str]

class MemorySearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    level: Optional[str] = Field(default=None, regex="^(L1|L2|L3)$")
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class MemorySearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    total_found: int
    search_time_ms: float

class SemanticSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    search_memories: bool = True
    search_concepts: bool = True
    limit: int = Field(default=10, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    use_reranking: bool = True

class MemoryStatsResponse(BaseModel):
    total: int
    by_level: Dict[str, Dict[str, Any]]
    avg_importance: float

class ConsolidationResponse(BaseModel):
    l1_to_l2: int
    l2_to_l3: int
    deleted: int
    timestamp: datetime

# Dependency pour récupérer les services
async def get_memory_service() -> MemoryService:
    """Dependency pour récupérer le service de mémoire"""
    # TODO: Intégrer avec l'injection de dépendances réelle
    # Pour l'instant, retourner None et gérer dans les routes
    return None

async def get_embedding_service() -> EmbeddingService:
    """Dependency pour récupérer le service d'embeddings"""
    # TODO: Intégrer avec l'injection de dépendances réelle
    return None

# Routes de gestion des mémoires
@router.post("/", response_model=MemoryResponse)
async def create_memory(
    request: CreateMemoryRequest,
    memory_service: MemoryServiceDep,
    user_id: CurrentUserDep
):
    """Create a new memory"""
    try:
        memory = await memory_service.create_memory(
            user_id=user_id,
            content=request.content,
            level=request.level,
            metadata=request.metadata
        )
        
        return MemoryResponse(
            id=memory["id"],
            content=memory["content"],
            level=memory["level"],
            importance=memory["importance"],
            metadata=memory["metadata"],
            created_at=memory["created_at"],
            updated_at=memory["updated_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create memory: {str(e)}"
        )

@router.get("/{memory_id}", response_model=MemoryResponse)
async def get_memory(
    memory_id: str,
    memory_service: MemoryServiceDep,
    user_id: CurrentUserDep
):
    """Get a specific memory by ID"""
    try:
        memory = await memory_service.get_memory(memory_id, user_id)
        
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Memory not found"
            )
        
        return MemoryResponse(
            id=memory["id"],
            content=memory["content"],
            level=memory["level"],
            importance=memory["importance"],
            metadata=memory["metadata"],
            created_at=memory["created_at"],
            updated_at=memory["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory: {str(e)}"
        )

@router.get("/search", response_model=List[MemoryResponse])
async def search_memories(
    query: str,
    level: Optional[MemoryLevel] = None,
    limit: int = 10,
    embedding_service: EmbeddingServiceDep,
    user_id: CurrentUserDep
):
    """Search memories using semantic search"""
    try:
        results = await embedding_service.search_memories(
            user_id=user_id,
            query=query,
            level=level,
            limit=limit
        )
        
        return [
            MemoryResponse(
                id=memory["id"],
                content=memory["content"],
                level=memory["level"],
                importance=memory["importance"],
                metadata=memory["metadata"],
                created_at=memory["created_at"],
                updated_at=memory["updated_at"]
            )
            for memory in results
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search memories: {str(e)}"
        )

@router.post("/search/semantic")
async def semantic_search(
    search_request: SemanticSearchRequest,
    embedding_service: EmbeddingServiceDep,
    user_id: CurrentUserDep
) -> Dict[str, Any]:
    """Hybrid semantic search in memories and concepts"""
    
    try:
        results = await embedding_service.semantic_search(
            user_id=user_id,
            query=search_request.query,
            search_memories=search_request.search_memories,
            search_concepts=search_request.search_concepts,
            limit=search_request.limit,
            similarity_threshold=search_request.similarity_threshold,
            use_reranking=search_request.use_reranking
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform semantic search: {str(e)}"
        )

@router.put("/{memory_id}/importance")
async def update_memory_importance(
    memory_id: str,
    importance: float = Field(..., ge=0.0, le=1.0),
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> Dict[str, Any]:
    """Met à jour l'importance d'une mémoire"""
    
    try:
        if not memory_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de mémoire non disponible"
            )
        
        user_id = UUID(current_user["user_id"])
        memory_uuid = UUID(memory_id)
        
        success = await memory_service.update_memory_importance(
            user_id, memory_uuid, importance
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mémoire non trouvée ou mise à jour échouée"
            )
        
        return {
            "message": "Importance mise à jour avec succès",
            "memory_id": memory_id,
            "new_importance": importance
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de mémoire ou importance invalide"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.post("/consolidate", response_model=ConsolidationResponse)
async def consolidate_memories(
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> ConsolidationResponse:
    """Lance la consolidation des mémoires L1->L2->L3"""
    
    try:
        if not memory_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de mémoire non disponible"
            )
        
        user_id = UUID(current_user["user_id"])
        
        stats = await memory_service.consolidate_memories(user_id)
        
        return ConsolidationResponse(
            l1_to_l2=stats["l1_to_l2"],
            l2_to_l3=stats["l2_to_l3"],
            deleted=stats["deleted"],
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la consolidation: {str(e)}"
        )

@router.get("/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service)
) -> MemoryStatsResponse:
    """Récupère les statistiques des mémoires de l'utilisateur"""
    
    try:
        if not memory_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service de mémoire non disponible"
            )
        
        user_id = UUID(current_user["user_id"])
        
        stats = await memory_service.get_memory_stats(user_id)
        
        return MemoryStatsResponse(**stats)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des stats: {str(e)}"
        )

@router.post("/{memory_id}/extract-concepts")
async def extract_concepts_from_memory(
    memory_id: str,
    auto_create: bool = Query(default=True, description="Créer automatiquement les concepts"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Extrait des concepts d'une mémoire et les lie au graphe"""
    
    try:
        if not memory_service or not embedding_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services non disponibles"
            )
        
        user_id = UUID(current_user["user_id"])
        memory_uuid = UUID(memory_id)
        
        # Récupérer la mémoire
        memory = await memory_service.get_memory_by_id(user_id, memory_uuid)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mémoire non trouvée"
            )
        
        # Extraire et lier les concepts
        concepts = await embedding_service.extract_and_link_concepts(
            user_id=user_id,
            memory_id=memory_uuid,
            content=memory["content"],
            auto_create_concepts=auto_create
        )
        
        return {
            "memory_id": memory_id,
            "extracted_concepts": concepts,
            "total_concepts": len(concepts)
        }
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de mémoire invalide"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'extraction de concepts: {str(e)}"
        )

@router.get("/{memory_id}/related")
async def get_related_content(
    memory_id: str,
    context_window: int = Query(default=5, ge=1, le=20),
    include_graph: bool = Query(default=True, description="Inclure les voisins du graphe"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    memory_service: MemoryService = Depends(get_memory_service),
    embedding_service: EmbeddingService = Depends(get_embedding_service)
) -> Dict[str, Any]:
    """Trouve du contenu lié à une mémoire"""
    
    try:
        if not memory_service or not embedding_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Services non disponibles"
            )
        
        user_id = UUID(current_user["user_id"])
        memory_uuid = UUID(memory_id)
        
        # Récupérer la mémoire
        memory = await memory_service.get_memory_by_id(user_id, memory_uuid)
        if not memory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Mémoire non trouvée"
            )
        
        # Trouver du contenu lié
        related_content = await embedding_service.find_related_content(
            user_id=user_id,
            content=memory["content"],
            context_window=context_window,
            include_graph_neighbors=include_graph
        )
        
        return related_content
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID de mémoire invalide"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la recherche de contenu lié: {str(e)}"
        )