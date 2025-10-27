"""
Routes de santé et monitoring pour l'API AGI
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from services.external_services import ExternalServicesManager
from services.memory_service import MemoryService
from services.graph_service import GraphService
from services.embedding_service import EmbeddingService

router = APIRouter(prefix="/health", tags=["health"])

async def get_services():
    """Dependency pour récupérer les services"""
    # Cette fonction sera mise à jour quand les services seront injectés
    pass

@router.get("/")
async def health_check() -> Dict[str, Any]:
    """Point de santé basique de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AGI Backend API",
        "version": "1.0.0"
    }

@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Point de santé détaillé avec vérification des services"""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "AGI Backend API",
        "version": "1.0.0",
        "services": {}
    }
    
    try:
        # TODO: Intégrer avec les vrais services une fois l'injection de dépendances configurée
        # Pour l'instant, retourner un statut de base
        
        health_status["services"] = {
            "database": {"status": "pending", "message": "Service non encore configuré"},
            "neo4j": {"status": "pending", "message": "Service non encore configuré"},
            "external_apis": {"status": "pending", "message": "Service non encore configuré"},
            "memory_service": {"status": "pending", "message": "Service non encore configuré"},
            "graph_service": {"status": "pending", "message": "Service non encore configuré"},
            "embedding_service": {"status": "pending", "message": "Service non encore configuré"}
        }
        
        return health_status
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
        return JSONResponse(
            status_code=503,
            content=health_status
        )

@router.get("/services/{service_name}")
async def service_health_check(service_name: str) -> Dict[str, Any]:
    """Point de santé pour un service spécifique"""
    
    valid_services = [
        "memory", "graph", "embedding", "external", "database", "neo4j"
    ]
    
    if service_name not in valid_services:
        raise HTTPException(
            status_code=404,
            detail=f"Service '{service_name}' non trouvé. Services disponibles: {valid_services}"
        )
    
    # TODO: Implémenter la vérification réelle des services
    return {
        "service": service_name,
        "status": "pending",
        "message": "Service non encore configuré",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """Métriques de base du système"""
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "uptime_seconds": 0,  # TODO: Calculer le vrai uptime
            "total_requests": 0,  # TODO: Implémenter le comptage des requêtes
            "active_connections": 0,  # TODO: Compter les connexions actives
            "memory_usage": {
                "total_memories": 0,  # TODO: Compter depuis la DB
                "l1_memories": 0,
                "l2_memories": 0,
                "l3_memories": 0
            },
            "graph_stats": {
                "total_concepts": 0,  # TODO: Compter depuis Neo4j
                "total_relations": 0
            }
        }
    }