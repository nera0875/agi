"""
MemoryConsolidationWorkflow - Workflow spécialisé pour la consolidation mémoire.

Responsabilités:
- Orchestrer le processus de consolidation L2 → L3
- Gérer la validation des mémoires consolidées
- Optimiser les connexions dans le graphe de connaissances
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from datetime import datetime, timedelta

from ..base_agent import BaseAgent, AgentConfig, AgentState
from ..consolidator_agent import ConsolidatorAgent
from ..validator_agent import ValidatorAgent
from ..connector_agent import ConnectorAgent
import structlog

logger = structlog.get_logger(__name__)


class MemoryConsolidationWorkflow(BaseAgent):
    """
    Workflow spécialisé pour la consolidation mémoire L2 → L3.
    
    Coordonne les agents ConsolidatorAgent, ValidatorAgent et ConnectorAgent
    pour un processus de consolidation mémoire optimisé.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Initialiser les agents spécialisés
        self.consolidator_agent = ConsolidatorAgent(config, services)
        self.validator_agent = ValidatorAgent(config, services)
        self.connector_agent = ConnectorAgent(config, services)
        
        # Services requis
        self.memory_service = services.get("memory_service")
        self.graph_service = services.get("graph_service")
        
        # Configuration du workflow
        self.consolidation_threshold_hours = 24  # Consolider les mémoires > 24h
        self.batch_size = 50  # Traiter par lots de 50 mémoires
        self.validation_threshold = 0.8  # Seuil de validation
        
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour la consolidation mémoire."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("identify_consolidation_candidates", self._identify_consolidation_candidates)
        workflow.add_node("batch_consolidation", self._batch_consolidation)
        workflow.add_node("validate_consolidated_memories", self._validate_consolidated_memories)
        workflow.add_node("update_memory_connections", self._update_memory_connections)
        workflow.add_node("cleanup_old_memories", self._cleanup_old_memories)
        workflow.add_node("generate_consolidation_report", self._generate_consolidation_report)
        
        # Définir les transitions
        workflow.set_entry_point("identify_consolidation_candidates")
        workflow.add_edge("identify_consolidation_candidates", "batch_consolidation")
        workflow.add_edge("batch_consolidation", "validate_consolidated_memories")
        workflow.add_edge("validate_consolidated_memories", "update_memory_connections")
        workflow.add_edge("update_memory_connections", "cleanup_old_memories")
        workflow.add_edge("cleanup_old_memories", "generate_consolidation_report")
        workflow.add_edge("generate_consolidation_report", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour la consolidation mémoire."""
        return await self.run(state)
    
    async def consolidate_memories(self, force_consolidation: bool = False) -> Dict[str, Any]:
        """Lancer le processus de consolidation mémoire."""
        
        # Créer l'état initial
        initial_state = AgentState(
            messages=[],
            context={
                "consolidation_start": datetime.now().isoformat(),
                "force_consolidation": force_consolidation,
                "consolidation_config": {
                    "threshold_hours": self.consolidation_threshold_hours,
                    "batch_size": self.batch_size,
                    "validation_threshold": self.validation_threshold
                }
            },
            step_count=0
        )
        
        # Exécuter le workflow
        result_state = await self.process(initial_state)
        
        return {
            "success": not result_state.get("error"),
            "consolidation_report": result_state.get("context", {}).get("consolidation_report"),
            "error": result_state.get("error"),
            "execution_time": result_state.get("context", {}).get("execution_time")
        }
    
    async def _identify_consolidation_candidates(self, state: AgentState) -> AgentState:
        """Identifier les mémoires candidates à la consolidation."""
        self._log_step("identify_consolidation_candidates", state)
        state = self._increment_step(state)
        
        try:
            force_consolidation = state["context"].get("force_consolidation", False)
            threshold_hours = state["context"]["consolidation_config"]["threshold_hours"]
            
            # Calculer la date seuil
            threshold_date = datetime.now() - timedelta(hours=threshold_hours)
            
            # Récupérer les mémoires L2 candidates
            if force_consolidation:
                # Forcer la consolidation de toutes les mémoires L2
                candidates = await self.memory_service.get_all_l2_memories()
            else:
                # Récupérer seulement les mémoires anciennes
                candidates = await self.memory_service.get_l2_memories_before_date(threshold_date)
            
            # Filtrer et prioriser les candidates
            prioritized_candidates = self._prioritize_consolidation_candidates(candidates)
            
            state["context"]["consolidation_candidates"] = prioritized_candidates
            state["context"]["total_candidates"] = len(prioritized_candidates)
            
            self.logger.info("Consolidation candidates identified",
                           total_candidates=len(prioritized_candidates),
                           force_consolidation=force_consolidation)
            
        except Exception as e:
            state["error"] = f"Candidate identification failed: {str(e)}"
            self.logger.error("Candidate identification failed", error=str(e))
        
        return state
    
    async def _batch_consolidation(self, state: AgentState) -> AgentState:
        """Consolider les mémoires par lots."""
        self._log_step("batch_consolidation", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            candidates = state["context"]["consolidation_candidates"]
            batch_size = state["context"]["consolidation_config"]["batch_size"]
            
            consolidated_memories = []
            consolidation_errors = []
            
            # Traiter par lots
            for i in range(0, len(candidates), batch_size):
                batch = candidates[i:i + batch_size]
                
                try:
                    # Créer l'état pour le ConsolidatorAgent
                    consolidator_state = AgentState(
                        messages=[],
                        context={
                            "l2_memories": batch,
                            "batch_number": i // batch_size + 1,
                            "total_batches": (len(candidates) + batch_size - 1) // batch_size
                        },
                        step_count=0
                    )
                    
                    # Exécuter la consolidation
                    result_state = await self.consolidator_agent.process(consolidator_state)
                    
                    if not result_state.get("error"):
                        batch_consolidated = result_state["context"].get("consolidated_memories", [])
                        consolidated_memories.extend(batch_consolidated)
                    else:
                        consolidation_errors.append({
                            "batch": i // batch_size + 1,
                            "error": result_state["error"]
                        })
                    
                except Exception as e:
                    consolidation_errors.append({
                        "batch": i // batch_size + 1,
                        "error": str(e)
                    })
            
            state["context"]["consolidated_memories"] = consolidated_memories
            state["context"]["consolidation_errors"] = consolidation_errors
            state["context"]["successful_consolidations"] = len(consolidated_memories)
            
            self.logger.info("Batch consolidation completed",
                           total_consolidated=len(consolidated_memories),
                           errors=len(consolidation_errors))
            
        except Exception as e:
            state["error"] = f"Batch consolidation failed: {str(e)}"
            self.logger.error("Batch consolidation failed", error=str(e))
        
        return state
    
    async def _validate_consolidated_memories(self, state: AgentState) -> AgentState:
        """Valider les mémoires consolidées."""
        self._log_step("validate_consolidated_memories", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            consolidated_memories = state["context"]["consolidated_memories"]
            validation_threshold = state["context"]["consolidation_config"]["validation_threshold"]
            
            if not consolidated_memories:
                state["context"]["validation_results"] = []
                return state
            
            # Créer l'état pour le ValidatorAgent
            validator_state = AgentState(
                messages=[],
                context={
                    "memories_to_validate": consolidated_memories,
                    "validation_threshold": validation_threshold,
                    "validation_type": "consolidation"
                },
                step_count=0
            )
            
            # Exécuter la validation
            result_state = await self.validator_agent.process(validator_state)
            
            if not result_state.get("error"):
                validation_results = result_state["context"].get("validation_results", [])
                
                # Filtrer les mémoires valides
                valid_memories = [
                    memory for memory, validation in zip(consolidated_memories, validation_results)
                    if validation.get("is_valid", False)
                ]
                
                invalid_memories = [
                    memory for memory, validation in zip(consolidated_memories, validation_results)
                    if not validation.get("is_valid", False)
                ]
                
                state["context"]["valid_consolidated_memories"] = valid_memories
                state["context"]["invalid_consolidated_memories"] = invalid_memories
                state["context"]["validation_results"] = validation_results
                
                self.logger.info("Memory validation completed",
                               valid_memories=len(valid_memories),
                               invalid_memories=len(invalid_memories))
            else:
                state["error"] = f"Memory validation failed: {result_state['error']}"
            
        except Exception as e:
            state["error"] = f"Memory validation failed: {str(e)}"
            self.logger.error("Memory validation failed", error=str(e))
        
        return state
    
    async def _update_memory_connections(self, state: AgentState) -> AgentState:
        """Mettre à jour les connexions dans le graphe de connaissances."""
        self._log_step("update_memory_connections", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            valid_memories = state["context"].get("valid_consolidated_memories", [])
            
            if not valid_memories:
                state["context"]["connection_updates"] = []
                return state
            
            # Créer l'état pour le ConnectorAgent
            connector_state = AgentState(
                messages=[],
                context={
                    "new_memories": valid_memories,
                    "update_type": "consolidation",
                    "focus_area": "memory_connections"
                },
                step_count=0
            )
            
            # Exécuter la mise à jour des connexions
            result_state = await self.connector_agent.process(connector_state)
            
            if not result_state.get("error"):
                connection_updates = result_state["context"]
                state["context"]["connection_updates"] = connection_updates
                
                self.logger.info("Memory connections updated",
                               created_connections=connection_updates.get("created_connections", 0),
                               optimized_connections=connection_updates.get("optimized_connections", 0))
            else:
                state["error"] = f"Connection update failed: {result_state['error']}"
            
        except Exception as e:
            state["error"] = f"Connection update failed: {str(e)}"
            self.logger.error("Connection update failed", error=str(e))
        
        return state
    
    async def _cleanup_old_memories(self, state: AgentState) -> AgentState:
        """Nettoyer les anciennes mémoires L2 consolidées."""
        self._log_step("cleanup_old_memories", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            valid_memories = state["context"].get("valid_consolidated_memories", [])
            candidates = state["context"]["consolidation_candidates"]
            
            # Identifier les mémoires L2 à supprimer
            consolidated_l2_ids = []
            for memory in valid_memories:
                source_l2_ids = memory.get("source_l2_memories", [])
                consolidated_l2_ids.extend(source_l2_ids)
            
            # Supprimer les mémoires L2 consolidées
            cleanup_results = []
            for l2_id in consolidated_l2_ids:
                try:
                    await self.memory_service.archive_l2_memory(l2_id)
                    cleanup_results.append({"id": l2_id, "status": "archived"})
                except Exception as e:
                    cleanup_results.append({"id": l2_id, "status": "error", "error": str(e)})
            
            state["context"]["cleanup_results"] = cleanup_results
            state["context"]["archived_memories"] = len([r for r in cleanup_results if r["status"] == "archived"])
            
            self.logger.info("Memory cleanup completed",
                           archived_memories=len([r for r in cleanup_results if r["status"] == "archived"]),
                           cleanup_errors=len([r for r in cleanup_results if r["status"] == "error"]))
            
        except Exception as e:
            state["error"] = f"Memory cleanup failed: {str(e)}"
            self.logger.error("Memory cleanup failed", error=str(e))
        
        return state
    
    async def _generate_consolidation_report(self, state: AgentState) -> AgentState:
        """Générer le rapport de consolidation."""
        self._log_step("generate_consolidation_report", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Calculer le temps d'exécution
            start_time = datetime.fromisoformat(state["context"]["consolidation_start"])
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Créer le rapport
            report = {
                "execution_summary": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "execution_time_seconds": execution_time,
                    "success": not state.get("error")
                },
                "consolidation_metrics": {
                    "total_candidates": state["context"].get("total_candidates", 0),
                    "successful_consolidations": state["context"].get("successful_consolidations", 0),
                    "valid_consolidated_memories": len(state["context"].get("valid_consolidated_memories", [])),
                    "invalid_consolidated_memories": len(state["context"].get("invalid_consolidated_memories", [])),
                    "archived_memories": state["context"].get("archived_memories", 0)
                },
                "connection_metrics": {
                    "created_connections": state["context"].get("connection_updates", {}).get("created_connections", 0),
                    "optimized_connections": state["context"].get("connection_updates", {}).get("optimized_connections", 0)
                },
                "errors": {
                    "consolidation_errors": len(state["context"].get("consolidation_errors", [])),
                    "validation_errors": len([r for r in state["context"].get("validation_results", []) if r.get("error")]),
                    "cleanup_errors": len([r for r in state["context"].get("cleanup_results", []) if r["status"] == "error"])
                },
                "recommendations": self._generate_consolidation_recommendations(state)
            }
            
            state["context"]["consolidation_report"] = report
            state["context"]["execution_time"] = execution_time
            
            self.logger.info("Consolidation report generated",
                           execution_time=execution_time,
                           successful_consolidations=report["consolidation_metrics"]["successful_consolidations"])
            
        except Exception as e:
            state["error"] = f"Report generation failed: {str(e)}"
            self.logger.error("Report generation failed", error=str(e))
        
        return state
    
    def _prioritize_consolidation_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioriser les candidates à la consolidation."""
        
        def priority_score(memory):
            score = 0
            
            # Âge de la mémoire (plus ancien = plus prioritaire)
            age_hours = (datetime.now() - datetime.fromisoformat(memory.get("created_at", datetime.now().isoformat()))).total_seconds() / 3600
            score += min(age_hours / 24, 10)  # Max 10 points pour l'âge
            
            # Fréquence d'accès (moins accédé = plus prioritaire pour consolidation)
            access_count = memory.get("access_count", 0)
            score += max(0, 5 - access_count)  # Max 5 points pour faible accès
            
            # Taille du contenu (plus gros = plus prioritaire)
            content_size = len(memory.get("content", ""))
            score += min(content_size / 1000, 3)  # Max 3 points pour la taille
            
            # Relations existantes (plus de relations = plus prioritaire)
            relation_count = memory.get("relation_count", 0)
            score += min(relation_count, 2)  # Max 2 points pour les relations
            
            return score
        
        # Trier par score de priorité (décroissant)
        return sorted(candidates, key=priority_score, reverse=True)
    
    def _generate_consolidation_recommendations(self, state: AgentState) -> List[str]:
        """Générer des recommandations basées sur les résultats de consolidation."""
        recommendations = []
        
        # Analyser les métriques
        metrics = state["context"].get("consolidation_report", {}).get("consolidation_metrics", {})
        errors = state["context"].get("consolidation_report", {}).get("errors", {})
        
        total_candidates = metrics.get("total_candidates", 0)
        successful_consolidations = metrics.get("successful_consolidations", 0)
        
        # Recommandations basées sur le taux de succès
        if total_candidates > 0:
            success_rate = successful_consolidations / total_candidates
            
            if success_rate < 0.5:
                recommendations.append("Low consolidation success rate - review consolidation criteria")
            elif success_rate > 0.9:
                recommendations.append("High consolidation success rate - consider more frequent consolidation")
        
        # Recommandations basées sur les erreurs
        if errors.get("consolidation_errors", 0) > 0:
            recommendations.append("Consolidation errors detected - review system resources and configuration")
        
        if errors.get("validation_errors", 0) > 0:
            recommendations.append("Validation errors detected - review validation criteria")
        
        # Recommandations basées sur les connexions
        connection_metrics = state["context"].get("connection_updates", {})
        created_connections = connection_metrics.get("created_connections", 0)
        
        if created_connections == 0:
            recommendations.append("No new connections created - review connection algorithms")
        
        # Recommandations générales
        if total_candidates > 1000:
            recommendations.append("Large number of candidates - consider more frequent consolidation cycles")
        
        return recommendations