"""
MultiAgentOrchestrator - Orchestrateur principal pour coordonner les agents multiples.

Responsabilités:
- Coordonner l'exécution des différents agents
- Gérer les dépendances entre agents
- Optimiser l'ordre d'exécution
- Gérer les conflits et la synchronisation
"""

from typing import Any, Dict, List, Optional, Set
from enum import Enum
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
import asyncio
import json
from datetime import datetime

from ..base_agent import BaseAgent, AgentConfig, AgentState
from ..consolidator_agent import ConsolidatorAgent
from ..validator_agent import ValidatorAgent
from ..pattern_extractor_agent import PatternExtractorAgent
from ..connector_agent import ConnectorAgent
import structlog

logger = structlog.get_logger(__name__)


class AgentType(Enum):
    """Types d'agents disponibles."""
    CONSOLIDATOR = "consolidator"
    VALIDATOR = "validator"
    PATTERN_EXTRACTOR = "pattern_extractor"
    CONNECTOR = "connector"


class ExecutionMode(Enum):
    """Modes d'exécution des agents."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    PIPELINE = "pipeline"


@dataclass
class AgentTask:
    """Tâche à exécuter par un agent."""
    agent_type: AgentType
    priority: int
    dependencies: List[AgentType]
    input_data: Dict[str, Any]
    timeout: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class ExecutionPlan:
    """Plan d'exécution pour les agents."""
    tasks: List[AgentTask]
    execution_mode: ExecutionMode
    total_timeout: Optional[int] = None
    parallel_limit: int = 2


class MultiAgentOrchestrator(BaseAgent):
    """
    Orchestrateur principal pour coordonner l'exécution des agents multiples.
    
    Gère l'ordre d'exécution, les dépendances, et la synchronisation
    entre les différents agents du système AGI.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Initialiser les agents
        self.agents = {}
        self._initialize_agents(services)
        
        # Configuration de l'orchestrateur
        self.max_parallel_agents = 2
        self.default_timeout = 300  # 5 minutes
        self.execution_history = []
        
        # Dépendances entre agents
        self.agent_dependencies = {
            AgentType.CONSOLIDATOR: [],
            AgentType.PATTERN_EXTRACTOR: [],
            AgentType.VALIDATOR: [AgentType.CONSOLIDATOR],
            AgentType.CONNECTOR: [AgentType.PATTERN_EXTRACTOR, AgentType.VALIDATOR]
        }
        
    def _initialize_agents(self, services: Dict[str, Any]):
        """Initialiser tous les agents."""
        try:
            # Configuration commune pour tous les agents
            base_config = AgentConfig(
                name="orchestrated_agent",
                version="1.0.0",
                description="Agent orchestré",
                max_iterations=10
            )
            
            # Initialiser chaque agent
            self.agents[AgentType.CONSOLIDATOR] = ConsolidatorAgent(base_config, services)
            self.agents[AgentType.VALIDATOR] = ValidatorAgent(base_config, services)
            self.agents[AgentType.PATTERN_EXTRACTOR] = PatternExtractorAgent(base_config, services)
            self.agents[AgentType.CONNECTOR] = ConnectorAgent(base_config, services)
            
            self.logger.info("All agents initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize agents", error=str(e))
            raise
    
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour l'orchestration."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("plan_execution", self._plan_execution)
        workflow.add_node("execute_agents", self._execute_agents)
        workflow.add_node("validate_results", self._validate_results)
        workflow.add_node("consolidate_outputs", self._consolidate_outputs)
        workflow.add_node("finalize_execution", self._finalize_execution)
        
        # Définir les transitions
        workflow.set_entry_point("plan_execution")
        workflow.add_edge("plan_execution", "execute_agents")
        workflow.add_edge("execute_agents", "validate_results")
        workflow.add_edge("validate_results", "consolidate_outputs")
        workflow.add_edge("consolidate_outputs", "finalize_execution")
        workflow.add_edge("finalize_execution", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour l'orchestration."""
        return await self.run(state)
    
    async def execute_workflow(self, workflow_type: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Exécuter un workflow spécifique."""
        
        # Créer l'état initial
        initial_state = AgentState(
            messages=[],
            context={
                "workflow_type": workflow_type,
                "input_data": input_data,
                "execution_start": datetime.now().isoformat()
            },
            step_count=0
        )
        
        # Exécuter le workflow
        result_state = await self.process(initial_state)
        
        return {
            "success": not result_state.get("error"),
            "results": result_state.get("context", {}),
            "error": result_state.get("error"),
            "execution_time": result_state.get("context", {}).get("execution_time")
        }
    
    async def _plan_execution(self, state: AgentState) -> AgentState:
        """Planifier l'exécution des agents."""
        self._log_step("plan_execution", state)
        state = self._increment_step(state)
        
        try:
            workflow_type = state["context"]["workflow_type"]
            input_data = state["context"]["input_data"]
            
            # Créer le plan d'exécution basé sur le type de workflow
            execution_plan = self._create_execution_plan(workflow_type, input_data)
            
            state["context"]["execution_plan"] = execution_plan
            state["context"]["planned_tasks"] = len(execution_plan.tasks)
            
            self.logger.info("Execution planning completed",
                           workflow_type=workflow_type,
                           planned_tasks=len(execution_plan.tasks),
                           execution_mode=execution_plan.execution_mode.value)
            
        except Exception as e:
            state["error"] = f"Execution planning failed: {str(e)}"
            self.logger.error("Execution planning failed", error=str(e))
        
        return state
    
    async def _execute_agents(self, state: AgentState) -> AgentState:
        """Exécuter les agents selon le plan."""
        self._log_step("execute_agents", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            execution_plan: ExecutionPlan = state["context"]["execution_plan"]
            
            # Exécuter selon le mode
            if execution_plan.execution_mode == ExecutionMode.SEQUENTIAL:
                results = await self._execute_sequential(execution_plan.tasks)
            elif execution_plan.execution_mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel(execution_plan.tasks)
            elif execution_plan.execution_mode == ExecutionMode.PIPELINE:
                results = await self._execute_pipeline(execution_plan.tasks)
            else:
                results = await self._execute_conditional(execution_plan.tasks)
            
            state["context"]["agent_results"] = results
            state["context"]["executed_agents"] = len(results)
            
            self.logger.info("Agent execution completed",
                           executed_agents=len(results),
                           successful_agents=len([r for r in results.values() if not r.get("error")]))
            
        except Exception as e:
            state["error"] = f"Agent execution failed: {str(e)}"
            self.logger.error("Agent execution failed", error=str(e))
        
        return state
    
    async def _validate_results(self, state: AgentState) -> AgentState:
        """Valider les résultats des agents."""
        self._log_step("validate_results", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            agent_results = state["context"]["agent_results"]
            
            validation_results = {}
            overall_success = True
            
            for agent_type, result in agent_results.items():
                validation = self._validate_agent_result(agent_type, result)
                validation_results[agent_type] = validation
                
                if not validation["valid"]:
                    overall_success = False
            
            state["context"]["validation_results"] = validation_results
            state["context"]["overall_validation_success"] = overall_success
            
            self.logger.info("Result validation completed",
                           overall_success=overall_success,
                           validated_agents=len(validation_results))
            
        except Exception as e:
            state["error"] = f"Result validation failed: {str(e)}"
            self.logger.error("Result validation failed", error=str(e))
        
        return state
    
    async def _consolidate_outputs(self, state: AgentState) -> AgentState:
        """Consolider les sorties des agents."""
        self._log_step("consolidate_outputs", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            agent_results = state["context"]["agent_results"]
            validation_results = state["context"]["validation_results"]
            
            # Consolider les résultats valides
            consolidated_output = {
                "summary": self._create_execution_summary(agent_results, validation_results),
                "data": self._merge_agent_outputs(agent_results),
                "metrics": self._calculate_execution_metrics(agent_results),
                "recommendations": self._generate_recommendations(agent_results, validation_results)
            }
            
            state["context"]["consolidated_output"] = consolidated_output
            
            self.logger.info("Output consolidation completed",
                           total_data_points=len(consolidated_output["data"]),
                           recommendations=len(consolidated_output["recommendations"]))
            
        except Exception as e:
            state["error"] = f"Output consolidation failed: {str(e)}"
            self.logger.error("Output consolidation failed", error=str(e))
        
        return state
    
    async def _finalize_execution(self, state: AgentState) -> AgentState:
        """Finaliser l'exécution."""
        self._log_step("finalize_execution", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Calculer le temps d'exécution total
            start_time = datetime.fromisoformat(state["context"]["execution_start"])
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Enregistrer dans l'historique
            execution_record = {
                "workflow_type": state["context"]["workflow_type"],
                "execution_time": execution_time,
                "success": not state.get("error"),
                "agents_executed": state["context"].get("executed_agents", 0),
                "timestamp": end_time.isoformat()
            }
            
            self.execution_history.append(execution_record)
            
            state["context"]["execution_time"] = execution_time
            state["context"]["execution_complete"] = True
            
            self.logger.info("Execution finalized",
                           execution_time=execution_time,
                           total_steps=state["step_count"])
            
        except Exception as e:
            state["error"] = f"Execution finalization failed: {str(e)}"
            self.logger.error("Execution finalization failed", error=str(e))
        
        return state
    
    def _create_execution_plan(self, workflow_type: str, input_data: Dict[str, Any]) -> ExecutionPlan:
        """Créer un plan d'exécution basé sur le type de workflow."""
        
        if workflow_type == "memory_consolidation":
            return self._create_memory_consolidation_plan(input_data)
        elif workflow_type == "knowledge_validation":
            return self._create_knowledge_validation_plan(input_data)
        elif workflow_type == "pattern_analysis":
            return self._create_pattern_analysis_plan(input_data)
        elif workflow_type == "full_processing":
            return self._create_full_processing_plan(input_data)
        else:
            # Plan par défaut
            return self._create_default_plan(input_data)
    
    def _create_memory_consolidation_plan(self, input_data: Dict[str, Any]) -> ExecutionPlan:
        """Plan pour la consolidation mémoire."""
        tasks = [
            AgentTask(
                agent_type=AgentType.CONSOLIDATOR,
                priority=1,
                dependencies=[],
                input_data=input_data
            ),
            AgentTask(
                agent_type=AgentType.VALIDATOR,
                priority=2,
                dependencies=[AgentType.CONSOLIDATOR],
                input_data=input_data
            )
        ]
        
        return ExecutionPlan(
            tasks=tasks,
            execution_mode=ExecutionMode.SEQUENTIAL
        )
    
    def _create_knowledge_validation_plan(self, input_data: Dict[str, Any]) -> ExecutionPlan:
        """Plan pour la validation des connaissances."""
        tasks = [
            AgentTask(
                agent_type=AgentType.VALIDATOR,
                priority=1,
                dependencies=[],
                input_data=input_data
            ),
            AgentTask(
                agent_type=AgentType.CONNECTOR,
                priority=2,
                dependencies=[AgentType.VALIDATOR],
                input_data=input_data
            )
        ]
        
        return ExecutionPlan(
            tasks=tasks,
            execution_mode=ExecutionMode.SEQUENTIAL
        )
    
    def _create_pattern_analysis_plan(self, input_data: Dict[str, Any]) -> ExecutionPlan:
        """Plan pour l'analyse de patterns."""
        tasks = [
            AgentTask(
                agent_type=AgentType.PATTERN_EXTRACTOR,
                priority=1,
                dependencies=[],
                input_data=input_data
            ),
            AgentTask(
                agent_type=AgentType.CONNECTOR,
                priority=2,
                dependencies=[AgentType.PATTERN_EXTRACTOR],
                input_data=input_data
            )
        ]
        
        return ExecutionPlan(
            tasks=tasks,
            execution_mode=ExecutionMode.SEQUENTIAL
        )
    
    def _create_full_processing_plan(self, input_data: Dict[str, Any]) -> ExecutionPlan:
        """Plan pour le traitement complet."""
        tasks = [
            AgentTask(
                agent_type=AgentType.CONSOLIDATOR,
                priority=1,
                dependencies=[],
                input_data=input_data
            ),
            AgentTask(
                agent_type=AgentType.PATTERN_EXTRACTOR,
                priority=1,
                dependencies=[],
                input_data=input_data
            ),
            AgentTask(
                agent_type=AgentType.VALIDATOR,
                priority=2,
                dependencies=[AgentType.CONSOLIDATOR],
                input_data=input_data
            ),
            AgentTask(
                agent_type=AgentType.CONNECTOR,
                priority=3,
                dependencies=[AgentType.PATTERN_EXTRACTOR, AgentType.VALIDATOR],
                input_data=input_data
            )
        ]
        
        return ExecutionPlan(
            tasks=tasks,
            execution_mode=ExecutionMode.PIPELINE
        )
    
    def _create_default_plan(self, input_data: Dict[str, Any]) -> ExecutionPlan:
        """Plan par défaut."""
        tasks = [
            AgentTask(
                agent_type=AgentType.PATTERN_EXTRACTOR,
                priority=1,
                dependencies=[],
                input_data=input_data
            )
        ]
        
        return ExecutionPlan(
            tasks=tasks,
            execution_mode=ExecutionMode.SEQUENTIAL
        )
    
    async def _execute_sequential(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Exécuter les tâches séquentiellement."""
        results = {}
        
        # Trier par priorité et dépendances
        sorted_tasks = self._sort_tasks_by_dependencies(tasks)
        
        for task in sorted_tasks:
            try:
                agent = self.agents[task.agent_type]
                
                # Créer l'état pour l'agent
                agent_state = AgentState(
                    messages=[],
                    context=task.input_data,
                    step_count=0
                )
                
                # Exécuter l'agent
                result_state = await agent.process(agent_state)
                
                results[task.agent_type.value] = {
                    "success": not result_state.get("error"),
                    "data": result_state.get("context", {}),
                    "error": result_state.get("error"),
                    "steps": result_state.get("step_count", 0)
                }
                
            except Exception as e:
                results[task.agent_type.value] = {
                    "success": False,
                    "error": str(e),
                    "data": {}
                }
        
        return results
    
    async def _execute_parallel(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Exécuter les tâches en parallèle."""
        results = {}
        
        # Grouper les tâches par niveau de dépendance
        task_levels = self._group_tasks_by_dependency_level(tasks)
        
        for level_tasks in task_levels:
            # Exécuter les tâches du même niveau en parallèle
            level_results = await asyncio.gather(
                *[self._execute_single_task(task) for task in level_tasks],
                return_exceptions=True
            )
            
            # Traiter les résultats
            for task, result in zip(level_tasks, level_results):
                if isinstance(result, Exception):
                    results[task.agent_type.value] = {
                        "success": False,
                        "error": str(result),
                        "data": {}
                    }
                else:
                    results[task.agent_type.value] = result
        
        return results
    
    async def _execute_pipeline(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Exécuter les tâches en pipeline."""
        results = {}
        pipeline_data = {}
        
        # Trier par priorité
        sorted_tasks = sorted(tasks, key=lambda t: t.priority)
        
        for task in sorted_tasks:
            try:
                # Enrichir les données d'entrée avec les résultats précédents
                enriched_input = {**task.input_data, **pipeline_data}
                
                agent = self.agents[task.agent_type]
                
                agent_state = AgentState(
                    messages=[],
                    context=enriched_input,
                    step_count=0
                )
                
                result_state = await agent.process(agent_state)
                
                result = {
                    "success": not result_state.get("error"),
                    "data": result_state.get("context", {}),
                    "error": result_state.get("error"),
                    "steps": result_state.get("step_count", 0)
                }
                
                results[task.agent_type.value] = result
                
                # Ajouter les données au pipeline pour les tâches suivantes
                if result["success"]:
                    pipeline_data.update(result["data"])
                
            except Exception as e:
                results[task.agent_type.value] = {
                    "success": False,
                    "error": str(e),
                    "data": {}
                }
        
        return results
    
    async def _execute_conditional(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """Exécuter les tâches conditionnellement."""
        # Pour l'instant, utiliser l'exécution séquentielle
        # Dans une implémentation complète, on ajouterait la logique conditionnelle
        return await self._execute_sequential(tasks)
    
    async def _execute_single_task(self, task: AgentTask) -> Dict[str, Any]:
        """Exécuter une tâche unique."""
        try:
            agent = self.agents[task.agent_type]
            
            agent_state = AgentState(
                messages=[],
                context=task.input_data,
                step_count=0
            )
            
            result_state = await agent.process(agent_state)
            
            return {
                "success": not result_state.get("error"),
                "data": result_state.get("context", {}),
                "error": result_state.get("error"),
                "steps": result_state.get("step_count", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "data": {}
            }
    
    def _sort_tasks_by_dependencies(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """Trier les tâches par dépendances."""
        sorted_tasks = []
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            # Trouver les tâches sans dépendances non satisfaites
            ready_tasks = []
            completed_agents = {task.agent_type for task in sorted_tasks}
            
            for task in remaining_tasks:
                if all(dep in completed_agents for dep in task.dependencies):
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Éviter les boucles infinies - prendre la première tâche
                ready_tasks = [remaining_tasks[0]]
            
            # Trier par priorité
            ready_tasks.sort(key=lambda t: t.priority)
            
            # Ajouter la première tâche prête
            task_to_add = ready_tasks[0]
            sorted_tasks.append(task_to_add)
            remaining_tasks.remove(task_to_add)
        
        return sorted_tasks
    
    def _group_tasks_by_dependency_level(self, tasks: List[AgentTask]) -> List[List[AgentTask]]:
        """Grouper les tâches par niveau de dépendance."""
        levels = []
        remaining_tasks = tasks.copy()
        completed_agents = set()
        
        while remaining_tasks:
            current_level = []
            
            for task in remaining_tasks[:]:
                if all(dep in completed_agents for dep in task.dependencies):
                    current_level.append(task)
                    remaining_tasks.remove(task)
            
            if not current_level:
                # Éviter les boucles infinies
                current_level = [remaining_tasks.pop(0)]
            
            levels.append(current_level)
            completed_agents.update(task.agent_type for task in current_level)
        
        return levels
    
    def _validate_agent_result(self, agent_type: str, result: Dict[str, Any]) -> Dict[str, Any]:
        """Valider le résultat d'un agent."""
        validation = {
            "valid": True,
            "issues": [],
            "score": 1.0
        }
        
        # Vérifications de base
        if not result.get("success", False):
            validation["valid"] = False
            validation["issues"].append("Agent execution failed")
            validation["score"] = 0.0
        
        if result.get("error"):
            validation["issues"].append(f"Error: {result['error']}")
            validation["score"] *= 0.5
        
        # Vérifications spécifiques par type d'agent
        data = result.get("data", {})
        
        if agent_type == AgentType.CONSOLIDATOR.value:
            if not data.get("consolidated_memories"):
                validation["issues"].append("No consolidated memories found")
                validation["score"] *= 0.7
        
        elif agent_type == AgentType.VALIDATOR.value:
            if "validation_results" not in data:
                validation["issues"].append("No validation results found")
                validation["score"] *= 0.7
        
        elif agent_type == AgentType.PATTERN_EXTRACTOR.value:
            if not data.get("extracted_patterns"):
                validation["issues"].append("No patterns extracted")
                validation["score"] *= 0.7
        
        elif agent_type == AgentType.CONNECTOR.value:
            if not data.get("created_connections"):
                validation["issues"].append("No connections created")
                validation["score"] *= 0.7
        
        # Ajuster la validité basée sur le score
        if validation["score"] < 0.5:
            validation["valid"] = False
        
        return validation
    
    def _create_execution_summary(self, agent_results: Dict[str, Any], 
                                validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Créer un résumé de l'exécution."""
        total_agents = len(agent_results)
        successful_agents = len([r for r in agent_results.values() if r.get("success")])
        valid_results = len([v for v in validation_results.values() if v.get("valid")])
        
        return {
            "total_agents": total_agents,
            "successful_agents": successful_agents,
            "valid_results": valid_results,
            "success_rate": successful_agents / total_agents if total_agents > 0 else 0,
            "validation_rate": valid_results / total_agents if total_agents > 0 else 0
        }
    
    def _merge_agent_outputs(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Fusionner les sorties des agents."""
        merged_data = {}
        
        for agent_type, result in agent_results.items():
            if result.get("success") and result.get("data"):
                merged_data[agent_type] = result["data"]
        
        return merged_data
    
    def _calculate_execution_metrics(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculer les métriques d'exécution."""
        total_steps = sum(r.get("steps", 0) for r in agent_results.values())
        avg_steps = total_steps / len(agent_results) if agent_results else 0
        
        return {
            "total_steps": total_steps,
            "average_steps_per_agent": avg_steps,
            "agents_with_errors": len([r for r in agent_results.values() if r.get("error")])
        }
    
    def _generate_recommendations(self, agent_results: Dict[str, Any], 
                                validation_results: Dict[str, Any]) -> List[str]:
        """Générer des recommandations basées sur les résultats."""
        recommendations = []
        
        # Analyser les échecs
        failed_agents = [agent for agent, result in agent_results.items() 
                        if not result.get("success")]
        
        if failed_agents:
            recommendations.append(f"Investigate failures in: {', '.join(failed_agents)}")
        
        # Analyser les validations
        invalid_results = [agent for agent, validation in validation_results.items() 
                          if not validation.get("valid")]
        
        if invalid_results:
            recommendations.append(f"Review validation issues for: {', '.join(invalid_results)}")
        
        # Recommandations générales
        if len(failed_agents) > len(agent_results) / 2:
            recommendations.append("Consider reviewing system configuration")
        
        return recommendations