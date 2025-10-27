"""
KnowledgeValidationWorkflow - Workflow spécialisé pour la validation des connaissances.

Responsabilités:
- Orchestrer la validation complète du graphe de connaissances
- Détecter et résoudre les contradictions
- Maintenir la cohérence des données
- Optimiser la qualité des connaissances
"""

from typing import Any, Dict, List, Optional, Set
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from datetime import datetime
from dataclasses import dataclass

from ..base_agent import BaseAgent, AgentConfig, AgentState
from ..validator_agent import ValidatorAgent
from ..connector_agent import ConnectorAgent
from ..pattern_extractor_agent import PatternExtractorAgent
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ValidationScope:
    """Définit la portée de la validation."""
    validate_memories: bool = True
    validate_connections: bool = True
    validate_patterns: bool = True
    validate_consistency: bool = True
    deep_validation: bool = False


@dataclass
class ValidationMetrics:
    """Métriques de validation."""
    total_items_validated: int = 0
    valid_items: int = 0
    invalid_items: int = 0
    contradictions_found: int = 0
    contradictions_resolved: int = 0
    patterns_validated: int = 0
    connections_validated: int = 0


class KnowledgeValidationWorkflow(BaseAgent):
    """
    Workflow spécialisé pour la validation complète des connaissances.
    
    Coordonne les agents ValidatorAgent, ConnectorAgent et PatternExtractorAgent
    pour assurer la cohérence et la qualité du graphe de connaissances.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Initialiser les agents spécialisés
        self.validator_agent = ValidatorAgent(config, services)
        self.connector_agent = ConnectorAgent(config, services)
        self.pattern_extractor_agent = PatternExtractorAgent(config, services)
        
        # Services requis
        self.memory_service = services.get("memory_service")
        self.graph_service = services.get("graph_service")
        
        # Configuration du workflow
        self.validation_batch_size = 100
        self.contradiction_threshold = 0.7
        self.consistency_threshold = 0.8
        self.max_validation_iterations = 3
        
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour la validation des connaissances."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("analyze_validation_scope", self._analyze_validation_scope)
        workflow.add_node("validate_memory_consistency", self._validate_memory_consistency)
        workflow.add_node("validate_connection_integrity", self._validate_connection_integrity)
        workflow.add_node("validate_pattern_coherence", self._validate_pattern_coherence)
        workflow.add_node("detect_global_contradictions", self._detect_global_contradictions)
        workflow.add_node("resolve_contradictions", self._resolve_contradictions)
        workflow.add_node("optimize_knowledge_quality", self._optimize_knowledge_quality)
        workflow.add_node("generate_validation_report", self._generate_validation_report)
        
        # Définir les transitions
        workflow.set_entry_point("analyze_validation_scope")
        workflow.add_edge("analyze_validation_scope", "validate_memory_consistency")
        workflow.add_edge("validate_memory_consistency", "validate_connection_integrity")
        workflow.add_edge("validate_connection_integrity", "validate_pattern_coherence")
        workflow.add_edge("validate_pattern_coherence", "detect_global_contradictions")
        workflow.add_edge("detect_global_contradictions", "resolve_contradictions")
        workflow.add_edge("resolve_contradictions", "optimize_knowledge_quality")
        workflow.add_edge("optimize_knowledge_quality", "generate_validation_report")
        workflow.add_edge("generate_validation_report", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour la validation des connaissances."""
        return await self.run(state)
    
    async def validate_knowledge_base(self, validation_scope: ValidationScope = None) -> Dict[str, Any]:
        """Lancer le processus de validation complète."""
        
        if validation_scope is None:
            validation_scope = ValidationScope()
        
        # Créer l'état initial
        initial_state = AgentState(
            messages=[],
            context={
                "validation_start": datetime.now().isoformat(),
                "validation_scope": validation_scope,
                "validation_config": {
                    "batch_size": self.validation_batch_size,
                    "contradiction_threshold": self.contradiction_threshold,
                    "consistency_threshold": self.consistency_threshold,
                    "max_iterations": self.max_validation_iterations
                },
                "validation_metrics": ValidationMetrics()
            },
            step_count=0
        )
        
        # Exécuter le workflow
        result_state = await self.process(initial_state)
        
        return {
            "success": not result_state.get("error"),
            "validation_report": result_state.get("context", {}).get("validation_report"),
            "metrics": result_state.get("context", {}).get("validation_metrics"),
            "error": result_state.get("error"),
            "execution_time": result_state.get("context", {}).get("execution_time")
        }
    
    async def _analyze_validation_scope(self, state: AgentState) -> AgentState:
        """Analyser la portée de la validation."""
        self._log_step("analyze_validation_scope", state)
        state = self._increment_step(state)
        
        try:
            validation_scope: ValidationScope = state["context"]["validation_scope"]
            
            # Analyser l'état actuel du système
            system_stats = await self._get_system_statistics()
            
            # Déterminer les priorités de validation
            validation_priorities = self._determine_validation_priorities(system_stats, validation_scope)
            
            # Estimer la charge de travail
            workload_estimate = self._estimate_validation_workload(system_stats, validation_scope)
            
            state["context"]["system_stats"] = system_stats
            state["context"]["validation_priorities"] = validation_priorities
            state["context"]["workload_estimate"] = workload_estimate
            
            self.logger.info("Validation scope analyzed",
                           total_memories=system_stats.get("total_memories", 0),
                           total_connections=system_stats.get("total_connections", 0),
                           estimated_workload=workload_estimate.get("total_items", 0))
            
        except Exception as e:
            state["error"] = f"Validation scope analysis failed: {str(e)}"
            self.logger.error("Validation scope analysis failed", error=str(e))
        
        return state
    
    async def _validate_memory_consistency(self, state: AgentState) -> AgentState:
        """Valider la cohérence des mémoires."""
        self._log_step("validate_memory_consistency", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            validation_scope: ValidationScope = state["context"]["validation_scope"]
            
            if not validation_scope.validate_memories:
                state["context"]["memory_validation_results"] = {"skipped": True}
                return state
            
            # Récupérer toutes les mémoires à valider
            memories_to_validate = await self._get_memories_for_validation()
            
            memory_validation_results = []
            batch_size = state["context"]["validation_config"]["batch_size"]
            
            # Traiter par lots
            for i in range(0, len(memories_to_validate), batch_size):
                batch = memories_to_validate[i:i + batch_size]
                
                # Créer l'état pour le ValidatorAgent
                validator_state = AgentState(
                    messages=[],
                    context={
                        "memories_to_validate": batch,
                        "validation_type": "memory_consistency",
                        "batch_number": i // batch_size + 1
                    },
                    step_count=0
                )
                
                # Exécuter la validation
                result_state = await self.validator_agent.process(validator_state)
                
                if not result_state.get("error"):
                    batch_results = result_state["context"].get("validation_results", [])
                    memory_validation_results.extend(batch_results)
                else:
                    self.logger.error("Memory validation batch failed", 
                                    batch=i // batch_size + 1, 
                                    error=result_state["error"])
            
            # Analyser les résultats
            valid_memories = [r for r in memory_validation_results if r.get("is_valid", False)]
            invalid_memories = [r for r in memory_validation_results if not r.get("is_valid", False)]
            
            state["context"]["memory_validation_results"] = {
                "total_validated": len(memory_validation_results),
                "valid_memories": len(valid_memories),
                "invalid_memories": len(invalid_memories),
                "validation_details": memory_validation_results
            }
            
            # Mettre à jour les métriques
            metrics: ValidationMetrics = state["context"]["validation_metrics"]
            metrics.total_items_validated += len(memory_validation_results)
            metrics.valid_items += len(valid_memories)
            metrics.invalid_items += len(invalid_memories)
            
            self.logger.info("Memory consistency validation completed",
                           total_validated=len(memory_validation_results),
                           valid=len(valid_memories),
                           invalid=len(invalid_memories))
            
        except Exception as e:
            state["error"] = f"Memory consistency validation failed: {str(e)}"
            self.logger.error("Memory consistency validation failed", error=str(e))
        
        return state
    
    async def _validate_connection_integrity(self, state: AgentState) -> AgentState:
        """Valider l'intégrité des connexions."""
        self._log_step("validate_connection_integrity", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            validation_scope: ValidationScope = state["context"]["validation_scope"]
            
            if not validation_scope.validate_connections:
                state["context"]["connection_validation_results"] = {"skipped": True}
                return state
            
            # Utiliser le ConnectorAgent pour analyser les connexions
            connector_state = AgentState(
                messages=[],
                context={
                    "validation_mode": True,
                    "focus_area": "connection_integrity"
                },
                step_count=0
            )
            
            result_state = await self.connector_agent.process(connector_state)
            
            if not result_state.get("error"):
                connection_analysis = result_state["context"]
                
                # Analyser les résultats
                connection_validation_results = {
                    "total_connections_analyzed": connection_analysis.get("graph_stats", {}).get("edge_count", 0),
                    "weak_connections": len(connection_analysis.get("missing_connections", [])),
                    "optimized_connections": connection_analysis.get("optimized_connections", 0),
                    "removed_connections": connection_analysis.get("removed_connections", 0),
                    "connection_quality_score": self._calculate_connection_quality_score(connection_analysis)
                }
                
                state["context"]["connection_validation_results"] = connection_validation_results
                
                # Mettre à jour les métriques
                metrics: ValidationMetrics = state["context"]["validation_metrics"]
                metrics.connections_validated = connection_validation_results["total_connections_analyzed"]
                
                self.logger.info("Connection integrity validation completed",
                               total_analyzed=connection_validation_results["total_connections_analyzed"],
                               quality_score=connection_validation_results["connection_quality_score"])
            else:
                state["error"] = f"Connection validation failed: {result_state['error']}"
            
        except Exception as e:
            state["error"] = f"Connection integrity validation failed: {str(e)}"
            self.logger.error("Connection integrity validation failed", error=str(e))
        
        return state
    
    async def _validate_pattern_coherence(self, state: AgentState) -> AgentState:
        """Valider la cohérence des patterns."""
        self._log_step("validate_pattern_coherence", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            validation_scope: ValidationScope = state["context"]["validation_scope"]
            
            if not validation_scope.validate_patterns:
                state["context"]["pattern_validation_results"] = {"skipped": True}
                return state
            
            # Utiliser le PatternExtractorAgent pour analyser les patterns
            pattern_extractor_state = AgentState(
                messages=[],
                context={
                    "validation_mode": True,
                    "focus_area": "pattern_coherence"
                },
                step_count=0
            )
            
            result_state = await self.pattern_extractor_agent.process(pattern_extractor_state)
            
            if not result_state.get("error"):
                pattern_analysis = result_state["context"]
                
                # Analyser les résultats
                pattern_validation_results = {
                    "total_patterns_analyzed": len(pattern_analysis.get("extracted_patterns", [])),
                    "coherent_patterns": len([p for p in pattern_analysis.get("extracted_patterns", []) 
                                            if p.get("confidence", 0) >= self.consistency_threshold]),
                    "incoherent_patterns": len([p for p in pattern_analysis.get("extracted_patterns", []) 
                                              if p.get("confidence", 0) < self.consistency_threshold]),
                    "pattern_quality_score": self._calculate_pattern_quality_score(pattern_analysis)
                }
                
                state["context"]["pattern_validation_results"] = pattern_validation_results
                
                # Mettre à jour les métriques
                metrics: ValidationMetrics = state["context"]["validation_metrics"]
                metrics.patterns_validated = pattern_validation_results["total_patterns_analyzed"]
                
                self.logger.info("Pattern coherence validation completed",
                               total_analyzed=pattern_validation_results["total_patterns_analyzed"],
                               coherent=pattern_validation_results["coherent_patterns"],
                               quality_score=pattern_validation_results["pattern_quality_score"])
            else:
                state["error"] = f"Pattern validation failed: {result_state['error']}"
            
        except Exception as e:
            state["error"] = f"Pattern coherence validation failed: {str(e)}"
            self.logger.error("Pattern coherence validation failed", error=str(e))
        
        return state
    
    async def _detect_global_contradictions(self, state: AgentState) -> AgentState:
        """Détecter les contradictions globales."""
        self._log_step("detect_global_contradictions", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Analyser les résultats de validation précédents
            memory_results = state["context"].get("memory_validation_results", {})
            connection_results = state["context"].get("connection_validation_results", {})
            pattern_results = state["context"].get("pattern_validation_results", {})
            
            # Détecter les contradictions entre différents types de données
            contradictions = []
            
            # Contradictions mémoire-pattern
            memory_pattern_contradictions = await self._detect_memory_pattern_contradictions(
                memory_results, pattern_results
            )
            contradictions.extend(memory_pattern_contradictions)
            
            # Contradictions connexion-mémoire
            connection_memory_contradictions = await self._detect_connection_memory_contradictions(
                connection_results, memory_results
            )
            contradictions.extend(connection_memory_contradictions)
            
            # Contradictions temporelles
            temporal_contradictions = await self._detect_temporal_contradictions()
            contradictions.extend(temporal_contradictions)
            
            # Classer les contradictions par sévérité
            classified_contradictions = self._classify_contradictions_by_severity(contradictions)
            
            state["context"]["global_contradictions"] = classified_contradictions
            state["context"]["contradiction_count"] = len(contradictions)
            
            # Mettre à jour les métriques
            metrics: ValidationMetrics = state["context"]["validation_metrics"]
            metrics.contradictions_found = len(contradictions)
            
            self.logger.info("Global contradiction detection completed",
                           total_contradictions=len(contradictions),
                           critical=len(classified_contradictions.get("critical", [])),
                           moderate=len(classified_contradictions.get("moderate", [])))
            
        except Exception as e:
            state["error"] = f"Global contradiction detection failed: {str(e)}"
            self.logger.error("Global contradiction detection failed", error=str(e))
        
        return state
    
    async def _resolve_contradictions(self, state: AgentState) -> AgentState:
        """Résoudre les contradictions détectées."""
        self._log_step("resolve_contradictions", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            classified_contradictions = state["context"].get("global_contradictions", {})
            
            resolution_results = {
                "resolved_contradictions": [],
                "unresolved_contradictions": [],
                "resolution_strategies": []
            }
            
            # Résoudre les contradictions critiques en priorité
            for severity in ["critical", "moderate", "minor"]:
                contradictions = classified_contradictions.get(severity, [])
                
                for contradiction in contradictions:
                    try:
                        # Utiliser le ValidatorAgent pour résoudre la contradiction
                        validator_state = AgentState(
                            messages=[],
                            context={
                                "contradiction_to_resolve": contradiction,
                                "resolution_mode": True,
                                "severity": severity
                            },
                            step_count=0
                        )
                        
                        result_state = await self.validator_agent.process(validator_state)
                        
                        if not result_state.get("error"):
                            resolution = result_state["context"].get("resolution_result")
                            if resolution and resolution.get("resolved", False):
                                resolution_results["resolved_contradictions"].append({
                                    "contradiction": contradiction,
                                    "resolution": resolution,
                                    "severity": severity
                                })
                            else:
                                resolution_results["unresolved_contradictions"].append({
                                    "contradiction": contradiction,
                                    "reason": resolution.get("reason", "Unknown"),
                                    "severity": severity
                                })
                        else:
                            resolution_results["unresolved_contradictions"].append({
                                "contradiction": contradiction,
                                "reason": result_state["error"],
                                "severity": severity
                            })
                    
                    except Exception as e:
                        resolution_results["unresolved_contradictions"].append({
                            "contradiction": contradiction,
                            "reason": str(e),
                            "severity": severity
                        })
            
            state["context"]["contradiction_resolution_results"] = resolution_results
            
            # Mettre à jour les métriques
            metrics: ValidationMetrics = state["context"]["validation_metrics"]
            metrics.contradictions_resolved = len(resolution_results["resolved_contradictions"])
            
            self.logger.info("Contradiction resolution completed",
                           resolved=len(resolution_results["resolved_contradictions"]),
                           unresolved=len(resolution_results["unresolved_contradictions"]))
            
        except Exception as e:
            state["error"] = f"Contradiction resolution failed: {str(e)}"
            self.logger.error("Contradiction resolution failed", error=str(e))
        
        return state
    
    async def _optimize_knowledge_quality(self, state: AgentState) -> AgentState:
        """Optimiser la qualité des connaissances."""
        self._log_step("optimize_knowledge_quality", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Analyser les résultats de validation pour identifier les optimisations
            optimization_opportunities = self._identify_optimization_opportunities(state)
            
            optimization_results = {
                "applied_optimizations": [],
                "failed_optimizations": [],
                "quality_improvements": {}
            }
            
            # Appliquer les optimisations identifiées
            for opportunity in optimization_opportunities:
                try:
                    result = await self._apply_optimization(opportunity)
                    if result.get("success", False):
                        optimization_results["applied_optimizations"].append({
                            "type": opportunity["type"],
                            "description": opportunity["description"],
                            "impact": result.get("impact", {})
                        })
                    else:
                        optimization_results["failed_optimizations"].append({
                            "type": opportunity["type"],
                            "reason": result.get("error", "Unknown")
                        })
                
                except Exception as e:
                    optimization_results["failed_optimizations"].append({
                        "type": opportunity["type"],
                        "reason": str(e)
                    })
            
            # Calculer l'amélioration globale de la qualité
            quality_improvements = await self._calculate_quality_improvements(state)
            optimization_results["quality_improvements"] = quality_improvements
            
            state["context"]["optimization_results"] = optimization_results
            
            self.logger.info("Knowledge quality optimization completed",
                           applied_optimizations=len(optimization_results["applied_optimizations"]),
                           failed_optimizations=len(optimization_results["failed_optimizations"]))
            
        except Exception as e:
            state["error"] = f"Knowledge quality optimization failed: {str(e)}"
            self.logger.error("Knowledge quality optimization failed", error=str(e))
        
        return state
    
    async def _generate_validation_report(self, state: AgentState) -> AgentState:
        """Générer le rapport de validation."""
        self._log_step("generate_validation_report", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Calculer le temps d'exécution
            start_time = datetime.fromisoformat(state["context"]["validation_start"])
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Créer le rapport complet
            validation_report = {
                "execution_summary": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "execution_time_seconds": execution_time,
                    "success": not state.get("error")
                },
                "validation_scope": state["context"]["validation_scope"].__dict__,
                "system_statistics": state["context"].get("system_stats", {}),
                "validation_results": {
                    "memory_validation": state["context"].get("memory_validation_results", {}),
                    "connection_validation": state["context"].get("connection_validation_results", {}),
                    "pattern_validation": state["context"].get("pattern_validation_results", {})
                },
                "contradiction_analysis": {
                    "contradictions_found": state["context"].get("contradiction_count", 0),
                    "contradictions_by_severity": state["context"].get("global_contradictions", {}),
                    "resolution_results": state["context"].get("contradiction_resolution_results", {})
                },
                "optimization_results": state["context"].get("optimization_results", {}),
                "metrics": state["context"]["validation_metrics"].__dict__,
                "recommendations": self._generate_validation_recommendations(state),
                "quality_score": self._calculate_overall_quality_score(state)
            }
            
            state["context"]["validation_report"] = validation_report
            state["context"]["execution_time"] = execution_time
            
            self.logger.info("Validation report generated",
                           execution_time=execution_time,
                           overall_quality_score=validation_report["quality_score"])
            
        except Exception as e:
            state["error"] = f"Validation report generation failed: {str(e)}"
            self.logger.error("Validation report generation failed", error=str(e))
        
        return state
    
    # Méthodes utilitaires
    
    async def _get_system_statistics(self) -> Dict[str, Any]:
        """Récupérer les statistiques du système."""
        try:
            stats = {}
            
            # Statistiques mémoire
            stats["total_memories"] = await self.memory_service.count_all_memories()
            stats["l2_memories"] = await self.memory_service.count_l2_memories()
            stats["l3_memories"] = await self.memory_service.count_l3_memories()
            
            # Statistiques graphe
            graph_stats = await self.graph_service.get_graph_statistics()
            stats.update(graph_stats)
            
            return stats
        except Exception as e:
            self.logger.error("Failed to get system statistics", error=str(e))
            return {}
    
    def _determine_validation_priorities(self, system_stats: Dict[str, Any], 
                                       validation_scope: ValidationScope) -> List[str]:
        """Déterminer les priorités de validation."""
        priorities = []
        
        # Prioriser basé sur la taille des données
        if system_stats.get("total_memories", 0) > 10000:
            priorities.append("memory_consistency")
        
        if system_stats.get("edge_count", 0) > 50000:
            priorities.append("connection_integrity")
        
        # Prioriser basé sur la portée
        if validation_scope.validate_consistency:
            priorities.append("global_consistency")
        
        if validation_scope.deep_validation:
            priorities.append("deep_analysis")
        
        return priorities
    
    def _estimate_validation_workload(self, system_stats: Dict[str, Any], 
                                    validation_scope: ValidationScope) -> Dict[str, Any]:
        """Estimer la charge de travail de validation."""
        workload = {"total_items": 0, "estimated_time_minutes": 0}
        
        if validation_scope.validate_memories:
            memory_count = system_stats.get("total_memories", 0)
            workload["total_items"] += memory_count
            workload["estimated_time_minutes"] += memory_count * 0.01  # 0.01 min par mémoire
        
        if validation_scope.validate_connections:
            connection_count = system_stats.get("edge_count", 0)
            workload["total_items"] += connection_count
            workload["estimated_time_minutes"] += connection_count * 0.005  # 0.005 min par connexion
        
        return workload
    
    async def _get_memories_for_validation(self) -> List[Dict[str, Any]]:
        """Récupérer les mémoires à valider."""
        try:
            # Pour l'instant, récupérer toutes les mémoires
            # Dans une implémentation complète, on pourrait filtrer par critères
            return await self.memory_service.get_all_memories()
        except Exception as e:
            self.logger.error("Failed to get memories for validation", error=str(e))
            return []
    
    def _calculate_connection_quality_score(self, connection_analysis: Dict[str, Any]) -> float:
        """Calculer le score de qualité des connexions."""
        total_connections = connection_analysis.get("graph_stats", {}).get("edge_count", 1)
        weak_connections = len(connection_analysis.get("missing_connections", []))
        removed_connections = connection_analysis.get("removed_connections", 0)
        
        # Score basé sur le ratio de connexions faibles et supprimées
        quality_score = 1.0 - ((weak_connections + removed_connections) / total_connections)
        return max(0.0, min(1.0, quality_score))
    
    def _calculate_pattern_quality_score(self, pattern_analysis: Dict[str, Any]) -> float:
        """Calculer le score de qualité des patterns."""
        patterns = pattern_analysis.get("extracted_patterns", [])
        if not patterns:
            return 0.0
        
        # Score basé sur la confiance moyenne des patterns
        total_confidence = sum(p.get("confidence", 0) for p in patterns)
        return total_confidence / len(patterns)
    
    async def _detect_memory_pattern_contradictions(self, memory_results: Dict[str, Any], 
                                                  pattern_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Détecter les contradictions entre mémoires et patterns."""
        contradictions = []
        
        # Implémentation simplifiée - dans un vrai système, 
        # on analyserait les incohérences sémantiques
        try:
            invalid_memories = memory_results.get("validation_details", [])
            incoherent_patterns = pattern_results.get("incoherent_patterns", 0)
            
            if invalid_memories and incoherent_patterns > 0:
                contradictions.append({
                    "type": "memory_pattern_mismatch",
                    "description": f"Found {len(invalid_memories)} invalid memories and {incoherent_patterns} incoherent patterns",
                    "severity": "moderate",
                    "affected_items": len(invalid_memories)
                })
        
        except Exception as e:
            self.logger.error("Failed to detect memory-pattern contradictions", error=str(e))
        
        return contradictions
    
    async def _detect_connection_memory_contradictions(self, connection_results: Dict[str, Any], 
                                                     memory_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Détecter les contradictions entre connexions et mémoires."""
        contradictions = []
        
        try:
            weak_connections = connection_results.get("weak_connections", 0)
            invalid_memories = memory_results.get("invalid_memories", 0)
            
            # Si beaucoup de mémoires invalides mais peu de connexions faibles, c'est suspect
            if invalid_memories > 10 and weak_connections < 5:
                contradictions.append({
                    "type": "connection_memory_inconsistency",
                    "description": f"High invalid memories ({invalid_memories}) but low weak connections ({weak_connections})",
                    "severity": "moderate",
                    "affected_items": invalid_memories
                })
        
        except Exception as e:
            self.logger.error("Failed to detect connection-memory contradictions", error=str(e))
        
        return contradictions
    
    async def _detect_temporal_contradictions(self) -> List[Dict[str, Any]]:
        """Détecter les contradictions temporelles."""
        contradictions = []
        
        try:
            # Analyser les incohérences temporelles dans les données
            temporal_inconsistencies = await self.graph_service.find_temporal_inconsistencies()
            
            for inconsistency in temporal_inconsistencies:
                contradictions.append({
                    "type": "temporal_contradiction",
                    "description": inconsistency.get("description", "Temporal inconsistency found"),
                    "severity": "critical" if inconsistency.get("impact", 0) > 0.8 else "moderate",
                    "affected_items": inconsistency.get("affected_count", 1)
                })
        
        except Exception as e:
            self.logger.error("Failed to detect temporal contradictions", error=str(e))
        
        return contradictions
    
    def _classify_contradictions_by_severity(self, contradictions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Classer les contradictions par sévérité."""
        classified = {"critical": [], "moderate": [], "minor": []}
        
        for contradiction in contradictions:
            severity = contradiction.get("severity", "minor")
            if severity in classified:
                classified[severity].append(contradiction)
            else:
                classified["minor"].append(contradiction)
        
        return classified
    
    def _identify_optimization_opportunities(self, state: AgentState) -> List[Dict[str, Any]]:
        """Identifier les opportunités d'optimisation."""
        opportunities = []
        
        # Analyser les résultats pour identifier les optimisations possibles
        memory_results = state["context"].get("memory_validation_results", {})
        connection_results = state["context"].get("connection_validation_results", {})
        
        # Optimisation des mémoires
        if memory_results.get("invalid_memories", 0) > 0:
            opportunities.append({
                "type": "memory_cleanup",
                "description": "Remove or fix invalid memories",
                "priority": "high",
                "estimated_impact": memory_results.get("invalid_memories", 0)
            })
        
        # Optimisation des connexions
        if connection_results.get("weak_connections", 0) > 0:
            opportunities.append({
                "type": "connection_strengthening",
                "description": "Strengthen weak connections",
                "priority": "medium",
                "estimated_impact": connection_results.get("weak_connections", 0)
            })
        
        return opportunities
    
    async def _apply_optimization(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """Appliquer une optimisation."""
        try:
            optimization_type = opportunity["type"]
            
            if optimization_type == "memory_cleanup":
                # Nettoyer les mémoires invalides
                cleaned_count = await self.memory_service.cleanup_invalid_memories()
                return {
                    "success": True,
                    "impact": {"cleaned_memories": cleaned_count}
                }
            
            elif optimization_type == "connection_strengthening":
                # Renforcer les connexions faibles
                strengthened_count = await self.graph_service.strengthen_weak_connections()
                return {
                    "success": True,
                    "impact": {"strengthened_connections": strengthened_count}
                }
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown optimization type: {optimization_type}"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_quality_improvements(self, state: AgentState) -> Dict[str, Any]:
        """Calculer les améliorations de qualité."""
        improvements = {}
        
        try:
            # Comparer les métriques avant/après
            metrics: ValidationMetrics = state["context"]["validation_metrics"]
            
            if metrics.total_items_validated > 0:
                improvements["validation_success_rate"] = metrics.valid_items / metrics.total_items_validated
            
            if metrics.contradictions_found > 0:
                improvements["contradiction_resolution_rate"] = metrics.contradictions_resolved / metrics.contradictions_found
            
            # Calculer l'amélioration globale
            improvements["overall_improvement"] = (
                improvements.get("validation_success_rate", 0) * 0.6 +
                improvements.get("contradiction_resolution_rate", 0) * 0.4
            )
        
        except Exception as e:
            self.logger.error("Failed to calculate quality improvements", error=str(e))
        
        return improvements
    
    def _generate_validation_recommendations(self, state: AgentState) -> List[str]:
        """Générer des recommandations basées sur les résultats de validation."""
        recommendations = []
        
        # Analyser les métriques
        metrics: ValidationMetrics = state["context"]["validation_metrics"]
        
        # Recommandations basées sur le taux de validation
        if metrics.total_items_validated > 0:
            success_rate = metrics.valid_items / metrics.total_items_validated
            
            if success_rate < 0.7:
                recommendations.append("Low validation success rate - review data quality processes")
            elif success_rate > 0.95:
                recommendations.append("High validation success rate - consider more stringent validation criteria")
        
        # Recommandations basées sur les contradictions
        if metrics.contradictions_found > 0:
            resolution_rate = metrics.contradictions_resolved / metrics.contradictions_found
            
            if resolution_rate < 0.5:
                recommendations.append("Low contradiction resolution rate - review resolution algorithms")
            
            if metrics.contradictions_found > 100:
                recommendations.append("High number of contradictions - investigate data sources")
        
        # Recommandations basées sur les optimisations
        optimization_results = state["context"].get("optimization_results", {})
        failed_optimizations = len(optimization_results.get("failed_optimizations", []))
        
        if failed_optimizations > 0:
            recommendations.append("Some optimizations failed - review system configuration")
        
        return recommendations
    
    def _calculate_overall_quality_score(self, state: AgentState) -> float:
        """Calculer le score de qualité global."""
        try:
            metrics: ValidationMetrics = state["context"]["validation_metrics"]
            
            # Score basé sur plusieurs facteurs
            validation_score = 0.0
            if metrics.total_items_validated > 0:
                validation_score = metrics.valid_items / metrics.total_items_validated
            
            contradiction_score = 1.0
            if metrics.contradictions_found > 0:
                contradiction_score = 1.0 - (metrics.contradictions_found / max(metrics.total_items_validated, 1))
            
            # Score global pondéré
            overall_score = (
                validation_score * 0.5 +
                contradiction_score * 0.3 +
                0.2  # Score de base pour l'exécution réussie
            )
            
            return max(0.0, min(1.0, overall_score))
        
        except Exception as e:
            self.logger.error("Failed to calculate overall quality score", error=str(e))
            return 0.0