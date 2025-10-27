"""
Agents API Routes - LangGraph Agents Management
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio

from ...agents.consolidator_agent import ConsolidatorAgent
from ...agents.validator_agent import ValidatorAgent
from ...agents.pattern_extractor_agent import PatternExtractorAgent
from ...agents.connector_agent import ConnectorAgent
from ...agents.workflows.multi_agent_orchestrator import MultiAgentOrchestrator
from ...agents.workflows.memory_consolidation_workflow import MemoryConsolidationWorkflow
from ...agents.workflows.knowledge_validation_workflow import KnowledgeValidationWorkflow
from ...agents.workflows.pattern_analysis_workflow import PatternAnalysisWorkflow, AnalysisScope
from ...agents.base_agent import AgentConfig, AgentState
from ..dependencies import get_services

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentRequest(BaseModel):
    agent_type: str = Field(..., description="Type d'agent: consolidator, validator, pattern_extractor, connector")
    input_data: Dict[str, Any] = Field(..., description="Données d'entrée pour l'agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexte additionnel")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration spécifique à l'agent")


class WorkflowRequest(BaseModel):
    workflow_type: str = Field(..., description="Type de workflow: memory_consolidation, knowledge_validation, pattern_analysis, multi_agent")
    parameters: Dict[str, Any] = Field(..., description="Paramètres du workflow")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration du workflow")


class AgentResponse(BaseModel):
    agent_type: str
    result: Dict[str, Any]
    execution_time: float
    status: str
    timestamp: str
    error: Optional[str] = None


class WorkflowResponse(BaseModel):
    workflow_type: str
    result: Dict[str, Any]
    execution_time: float
    status: str
    timestamp: str
    agents_used: List[str]
    error: Optional[str] = None


@router.post("/execute", response_model=AgentResponse)
async def execute_agent(
    agent_request: AgentRequest, 
    services: Dict[str, Any] = Depends(get_services)
):
    """Exécuter un agent spécifique"""
    start_time = datetime.now()
    
    try:
        # Configuration de l'agent
        config = AgentConfig(
            name=f"{agent_request.agent_type}_agent",
            description=f"Agent {agent_request.agent_type}",
            **agent_request.config if agent_request.config else {}
        )
        
        # Créer l'état initial
        initial_state = AgentState(
            messages=[],
            context={
                "input_data": agent_request.input_data,
                "additional_context": agent_request.context or {},
                "execution_start": start_time.isoformat()
            },
            step_count=0
        )
        
        # Sélectionner et exécuter l'agent approprié
        agent = None
        if agent_request.agent_type == "consolidator":
            agent = ConsolidatorAgent(config, services)
        elif agent_request.agent_type == "validator":
            agent = ValidatorAgent(config, services)
        elif agent_request.agent_type == "pattern_extractor":
            agent = PatternExtractorAgent(config, services)
        elif agent_request.agent_type == "connector":
            agent = ConnectorAgent(config, services)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Agent type '{agent_request.agent_type}' not supported"
            )
        
        # Exécuter l'agent
        result_state = await agent.process(initial_state)
        
        # Calculer le temps d'exécution
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Préparer la réponse
        status = "completed" if not result_state.get("error") else "failed"
        
        return AgentResponse(
            agent_type=agent_request.agent_type,
            result=result_state.get("context", {}),
            execution_time=execution_time,
            status=status,
            timestamp=end_time.isoformat(),
            error=result_state.get("error")
        )
    
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.error(f"Failed to execute agent {agent_request.agent_type}: {e}")
        
        return AgentResponse(
            agent_type=agent_request.agent_type,
            result={},
            execution_time=execution_time,
            status="failed",
            timestamp=end_time.isoformat(),
            error=str(e)
        )


@router.post("/workflow", response_model=WorkflowResponse)
async def execute_workflow(
    workflow_request: WorkflowRequest,
    services: Dict[str, Any] = Depends(get_services)
):
    """Exécuter un workflow multi-agents"""
    start_time = datetime.now()
    
    try:
        workflow = None
        agents_used = []
        
        if workflow_request.workflow_type == "memory_consolidation":
            workflow = MemoryConsolidationWorkflow(services)
            agents_used = ["consolidator", "validator", "connector"]
            
            # Paramètres spécifiques pour la consolidation mémoire
            batch_size = workflow_request.parameters.get("batch_size", 100)
            threshold = workflow_request.parameters.get("threshold", 0.8)
            
            result = await workflow.run_consolidation(
                batch_size=batch_size,
                threshold=threshold,
                config=workflow_request.config or {}
            )
            
        elif workflow_request.workflow_type == "knowledge_validation":
            workflow = KnowledgeValidationWorkflow(services)
            agents_used = ["validator", "connector", "pattern_extractor"]
            
            # Paramètres spécifiques pour la validation
            scope = workflow_request.parameters.get("scope", "full")
            validation_level = workflow_request.parameters.get("validation_level", "comprehensive")
            
            result = await workflow.run_validation(
                scope=scope,
                validation_level=validation_level,
                config=workflow_request.config or {}
            )
            
        elif workflow_request.workflow_type == "pattern_analysis":
            workflow = PatternAnalysisWorkflow(services)
            agents_used = ["pattern_extractor", "connector", "validator"]
            
            # Paramètres spécifiques pour l'analyse de patterns
            analysis_scope = AnalysisScope(
                data_sources=workflow_request.parameters.get("data_sources", []),
                time_range=workflow_request.parameters.get("time_range"),
                pattern_types=workflow_request.parameters.get("pattern_types", ["all"]),
                depth_level=workflow_request.parameters.get("depth_level", "comprehensive")
            )
            
            result = await workflow.run_analysis(
                scope=analysis_scope,
                config=workflow_request.config or {}
            )
            
        elif workflow_request.workflow_type == "multi_agent":
            orchestrator = MultiAgentOrchestrator(services)
            agents_used = ["consolidator", "validator", "pattern_extractor", "connector"]
            
            # Paramètres pour l'orchestration multi-agents
            execution_mode = workflow_request.parameters.get("execution_mode", "sequential")
            workflow_type = workflow_request.parameters.get("workflow_type", "full_processing")
            
            result = await orchestrator.execute_workflow(
                workflow_type=workflow_type,
                execution_mode=execution_mode,
                parameters=workflow_request.parameters,
                config=workflow_request.config or {}
            )
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Workflow type '{workflow_request.workflow_type}' not supported"
            )
        
        # Calculer le temps d'exécution
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Préparer la réponse
        status = "completed" if not result.get("error") else "failed"
        
        return WorkflowResponse(
            workflow_type=workflow_request.workflow_type,
            result=result,
            execution_time=execution_time,
            status=status,
            timestamp=end_time.isoformat(),
            agents_used=agents_used,
            error=result.get("error")
        )
        
    except Exception as e:
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        logger.error(f"Failed to execute workflow {workflow_request.workflow_type}: {e}")
        
        return WorkflowResponse(
            workflow_type=workflow_request.workflow_type,
            result={},
            execution_time=execution_time,
            status="failed",
            timestamp=end_time.isoformat(),
            agents_used=[],
            error=str(e)
        )


@router.get("/status")
async def get_agents_status():
    """Obtenir le statut de tous les agents disponibles"""
    return {
        "available_agents": [
            {
                "name": "consolidator",
                "description": "Consolide la mémoire L2→L3 avec Claude",
                "status": "available",
                "capabilities": ["memory_consolidation", "pattern_identification", "claude_integration"]
            },
            {
                "name": "validator", 
                "description": "Détecte les contradictions et valide les informations",
                "status": "available",
                "capabilities": ["contradiction_detection", "consistency_validation", "conflict_resolution"]
            },
            {
                "name": "pattern_extractor",
                "description": "Extrait les patterns et concepts des données",
                "status": "available",
                "capabilities": ["pattern_extraction", "concept_identification", "trend_analysis"]
            },
            {
                "name": "connector",
                "description": "Gère les connexions du graphe de connaissances",
                "status": "available",
                "capabilities": ["graph_optimization", "connection_management", "relationship_analysis"]
            }
        ],
        "available_workflows": [
            {
                "name": "memory_consolidation",
                "description": "Workflow de consolidation mémoire L2→L3",
                "agents": ["consolidator", "validator", "connector"]
            },
            {
                "name": "knowledge_validation",
                "description": "Workflow de validation des connaissances",
                "agents": ["validator", "connector", "pattern_extractor"]
            },
            {
                "name": "pattern_analysis",
                "description": "Workflow d'analyse des patterns",
                "agents": ["pattern_extractor", "connector", "validator"]
            },
            {
                "name": "multi_agent",
                "description": "Orchestration multi-agents complète",
                "agents": ["consolidator", "validator", "pattern_extractor", "connector"]
            }
        ],
        "total_agents": 4,
        "total_workflows": 4
    }


@router.get("/health")
async def agents_health_check():
    """Vérification de santé du système d'agents"""
    try:
        # Vérifier la disponibilité des services
        # Cette vérification sera plus détaillée avec les vrais services
        
        return {
            "status": "healthy",
            "agents_initialized": True,
            "langgraph_ready": True,
            "workflows_available": True,
            "services": {
                "memory_service": "available",
                "claude_service": "available", 
                "vector_service": "available",
                "graph_service": "available"
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@router.get("/agents/{agent_type}/info")
async def get_agent_info(agent_type: str):
    """Obtenir des informations détaillées sur un agent spécifique"""
    
    agent_info = {
        "consolidator": {
            "name": "ConsolidatorAgent",
            "description": "Agent responsable de la consolidation de la mémoire L2 vers L3",
            "capabilities": [
                "Analyse des données L2",
                "Identification des patterns de consolidation",
                "Intégration avec Claude pour la consolidation",
                "Stockage des données L3",
                "Nettoyage des données L2 obsolètes"
            ],
            "input_format": {
                "memory_data": "List[Dict] - Données mémoire L2 à consolider",
                "consolidation_threshold": "float - Seuil de consolidation (0.0-1.0)",
                "batch_size": "int - Taille des lots de traitement"
            },
            "output_format": {
                "consolidated_memories": "List[Dict] - Mémoires L3 consolidées",
                "consolidation_report": "Dict - Rapport de consolidation",
                "cleanup_summary": "Dict - Résumé du nettoyage"
            }
        },
        "validator": {
            "name": "ValidatorAgent", 
            "description": "Agent responsable de la validation et détection de contradictions",
            "capabilities": [
                "Détection de contradictions",
                "Validation de cohérence",
                "Résolution de conflits",
                "Maintien de l'intégrité des connaissances"
            ],
            "input_format": {
                "knowledge_data": "List[Dict] - Données à valider",
                "validation_scope": "str - Portée de validation",
                "conflict_resolution_strategy": "str - Stratégie de résolution"
            },
            "output_format": {
                "validation_results": "Dict - Résultats de validation",
                "contradictions_found": "List[Dict] - Contradictions détectées",
                "resolution_actions": "List[Dict] - Actions de résolution"
            }
        },
        "pattern_extractor": {
            "name": "PatternExtractorAgent",
            "description": "Agent responsable de l'extraction de patterns et concepts",
            "capabilities": [
                "Extraction de patterns basiques",
                "Analyse sémantique",
                "Extraction de concepts",
                "Analyse des relations",
                "Identification de tendances"
            ],
            "input_format": {
                "data_sources": "List[str] - Sources de données",
                "pattern_types": "List[str] - Types de patterns à extraire",
                "analysis_depth": "str - Profondeur d'analyse"
            },
            "output_format": {
                "extracted_patterns": "List[Dict] - Patterns extraits",
                "concepts": "List[Dict] - Concepts identifiés",
                "relationships": "List[Dict] - Relations découvertes"
            }
        },
        "connector": {
            "name": "ConnectorAgent",
            "description": "Agent responsable de la gestion du graphe de connaissances",
            "capabilities": [
                "Analyse de la structure du graphe",
                "Identification de connexions manquantes",
                "Création de nouvelles connexions",
                "Optimisation des connexions existantes",
                "Mise à jour des métadonnées"
            ],
            "input_format": {
                "graph_data": "Dict - Données du graphe",
                "optimization_level": "str - Niveau d'optimisation",
                "connection_types": "List[str] - Types de connexions"
            },
            "output_format": {
                "graph_analysis": "Dict - Analyse du graphe",
                "new_connections": "List[Dict] - Nouvelles connexions",
                "optimization_report": "Dict - Rapport d'optimisation"
            }
        }
    }
    
    if agent_type not in agent_info:
        raise HTTPException(
            status_code=404,
            detail=f"Agent type '{agent_type}' not found"
        )
    
    return agent_info[agent_type]