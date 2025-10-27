"""
ValidatorAgent - Détection de contradictions et validation des connaissances.

Responsabilités:
- Détecter les contradictions dans les connaissances existantes
- Valider la cohérence des nouvelles informations
- Résoudre les conflits entre différentes sources
- Maintenir l'intégrité du système de connaissances
"""

from typing import Any, Dict, List, Optional, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
import json

from .base_agent import BaseAgent, AgentConfig, AgentState
from ..services.memory_service import MemoryService
from ..services.embedding_service import EmbeddingService
from ..services.graph_service import GraphService
import structlog

logger = structlog.get_logger(__name__)


class ValidationResult:
    """Résultat d'une validation."""
    def __init__(self, is_valid: bool, confidence: float, issues: List[str] = None, suggestions: List[str] = None):
        self.is_valid = is_valid
        self.confidence = confidence
        self.issues = issues or []
        self.suggestions = suggestions or []


class ValidatorAgent(BaseAgent):
    """
    Agent responsable de la validation et détection de contradictions.
    
    Utilise Claude et des techniques de comparaison sémantique pour
    identifier les incohérences et maintenir l'intégrité des connaissances.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Services requis
        self.memory_service: MemoryService = services.get("memory_service")
        self.embedding_service: EmbeddingService = services.get("embedding_service")
        self.graph_service: GraphService = services.get("graph_service")
        
        # Claude LLM pour validation
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Seuils de validation
        self.contradiction_threshold = 0.7  # Seuil pour détecter les contradictions
        self.similarity_threshold = 0.8     # Seuil pour identifier les contenus similaires
        self.confidence_threshold = 0.6     # Seuil minimum de confiance
        
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour la validation."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("prepare_validation", self._prepare_validation)
        workflow.add_node("detect_contradictions", self._detect_contradictions)
        workflow.add_node("validate_consistency", self._validate_consistency)
        workflow.add_node("resolve_conflicts", self._resolve_conflicts)
        workflow.add_node("update_knowledge", self._update_knowledge)
        
        # Définir les transitions
        workflow.set_entry_point("prepare_validation")
        workflow.add_edge("prepare_validation", "detect_contradictions")
        workflow.add_edge("detect_contradictions", "validate_consistency")
        workflow.add_edge("validate_consistency", "resolve_conflicts")
        workflow.add_edge("resolve_conflicts", "update_knowledge")
        workflow.add_edge("update_knowledge", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour la validation."""
        return await self.run(state)
    
    async def _prepare_validation(self, state: AgentState) -> AgentState:
        """Préparer les données pour la validation."""
        self._log_step("prepare_validation", state)
        state = self._increment_step(state)
        
        try:
            # Récupérer le contenu à valider depuis le contexte
            content_to_validate = state["context"].get("content_to_validate")
            validation_type = state["context"].get("validation_type", "new_knowledge")
            
            if not content_to_validate:
                state["error"] = "No content to validate provided"
                return state
            
            # Rechercher des connaissances similaires existantes
            similar_knowledge = await self._find_similar_knowledge(content_to_validate)
            
            state["context"]["similar_knowledge"] = similar_knowledge
            state["context"]["validation_prepared"] = True
            
            self.logger.info("Validation preparation completed",
                           similar_count=len(similar_knowledge),
                           validation_type=validation_type)
            
        except Exception as e:
            state["error"] = f"Validation preparation failed: {str(e)}"
            self.logger.error("Validation preparation failed", error=str(e))
        
        return state
    
    async def _detect_contradictions(self, state: AgentState) -> AgentState:
        """Détecter les contradictions potentielles."""
        self._log_step("detect_contradictions", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            content_to_validate = state["context"]["content_to_validate"]
            similar_knowledge = state["context"].get("similar_knowledge", [])
            
            contradictions = []
            
            for knowledge in similar_knowledge:
                # Analyser avec Claude pour détecter les contradictions
                contradiction_analysis = await self._analyze_contradiction(
                    content_to_validate, knowledge
                )
                
                if contradiction_analysis["has_contradiction"]:
                    contradictions.append({
                        "knowledge_id": knowledge["id"],
                        "knowledge_content": knowledge["content"],
                        "contradiction_type": contradiction_analysis["type"],
                        "severity": contradiction_analysis["severity"],
                        "explanation": contradiction_analysis["explanation"]
                    })
            
            state["context"]["contradictions"] = contradictions
            state["context"]["contradiction_count"] = len(contradictions)
            
            self.logger.info("Contradiction detection completed",
                           contradictions_found=len(contradictions))
            
        except Exception as e:
            state["error"] = f"Contradiction detection failed: {str(e)}"
            self.logger.error("Contradiction detection failed", error=str(e))
        
        return state
    
    async def _validate_consistency(self, state: AgentState) -> AgentState:
        """Valider la cohérence globale."""
        self._log_step("validate_consistency", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            content_to_validate = state["context"]["content_to_validate"]
            contradictions = state["context"].get("contradictions", [])
            
            # Validation de cohérence avec Claude
            consistency_result = await self._validate_with_claude(
                content_to_validate, contradictions
            )
            
            state["context"]["consistency_result"] = consistency_result
            state["context"]["is_consistent"] = consistency_result["is_consistent"]
            
            self.logger.info("Consistency validation completed",
                           is_consistent=consistency_result["is_consistent"],
                           confidence=consistency_result["confidence"])
            
        except Exception as e:
            state["error"] = f"Consistency validation failed: {str(e)}"
            self.logger.error("Consistency validation failed", error=str(e))
        
        return state
    
    async def _resolve_conflicts(self, state: AgentState) -> AgentState:
        """Résoudre les conflits détectés."""
        self._log_step("resolve_conflicts", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            contradictions = state["context"].get("contradictions", [])
            content_to_validate = state["context"]["content_to_validate"]
            
            resolutions = []
            
            for contradiction in contradictions:
                # Proposer une résolution avec Claude
                resolution = await self._propose_resolution(
                    content_to_validate, contradiction
                )
                resolutions.append(resolution)
            
            state["context"]["resolutions"] = resolutions
            state["context"]["conflicts_resolved"] = len(resolutions)
            
            self.logger.info("Conflict resolution completed",
                           resolutions_proposed=len(resolutions))
            
        except Exception as e:
            state["error"] = f"Conflict resolution failed: {str(e)}"
            self.logger.error("Conflict resolution failed", error=str(e))
        
        return state
    
    async def _update_knowledge(self, state: AgentState) -> AgentState:
        """Mettre à jour les connaissances selon les résolutions."""
        self._log_step("update_knowledge", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            resolutions = state["context"].get("resolutions", [])
            consistency_result = state["context"].get("consistency_result", {})
            
            updates_applied = 0
            
            # Appliquer les résolutions approuvées
            for resolution in resolutions:
                if resolution["action"] == "update_existing":
                    await self.memory_service.update_knowledge(
                        knowledge_id=resolution["target_id"],
                        new_content=resolution["updated_content"],
                        metadata=resolution["metadata"]
                    )
                    updates_applied += 1
                elif resolution["action"] == "mark_deprecated":
                    await self.memory_service.mark_as_deprecated(
                        knowledge_id=resolution["target_id"],
                        reason=resolution["reason"]
                    )
                    updates_applied += 1
            
            # Stocker le nouveau contenu si validé
            if consistency_result.get("is_consistent", False):
                await self.memory_service.store_validated_knowledge(
                    content=state["context"]["content_to_validate"],
                    validation_score=consistency_result["confidence"],
                    metadata={"validated_by": "ValidatorAgent"}
                )
            
            state["context"]["updates_applied"] = updates_applied
            state["context"]["validation_complete"] = True
            
            self.logger.info("Knowledge update completed",
                           updates_applied=updates_applied)
            
        except Exception as e:
            state["error"] = f"Knowledge update failed: {str(e)}"
            self.logger.error("Knowledge update failed", error=str(e))
        
        return state
    
    async def _find_similar_knowledge(self, content: str) -> List[Dict]:
        """Trouver des connaissances similaires pour comparaison."""
        try:
            # Obtenir l'embedding du contenu
            embedding = await self.embedding_service.get_embedding(content)
            
            # Rechercher des connaissances similaires
            similar_results = await self.memory_service.search_similar_knowledge(
                embedding=embedding,
                threshold=self.similarity_threshold,
                limit=10
            )
            
            return similar_results
            
        except Exception as e:
            self.logger.error("Similar knowledge search failed", error=str(e))
            return []
    
    async def _analyze_contradiction(self, new_content: str, existing_knowledge: Dict) -> Dict:
        """Analyser si deux contenus sont contradictoires."""
        
        prompt = f"""
Analysez si ces deux contenus sont contradictoires:

NOUVEAU CONTENU:
{new_content}

CONTENU EXISTANT:
{existing_knowledge['content']}

Évaluez:
1. Y a-t-il une contradiction directe?
2. Quel type de contradiction (factuelle, logique, temporelle)?
3. Quelle est la sévérité (faible, moyenne, élevée)?
4. Explication détaillée

Format JSON:
{{
    "has_contradiction": boolean,
    "type": "factual|logical|temporal|none",
    "severity": "low|medium|high",
    "explanation": "explication détaillée",
    "confidence": float
}}
"""
        
        messages = [
            SystemMessage(content=self._get_contradiction_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "has_contradiction": False,
                "type": "none",
                "severity": "low",
                "explanation": "Failed to parse analysis",
                "confidence": 0.0
            }
    
    async def _validate_with_claude(self, content: str, contradictions: List[Dict]) -> Dict:
        """Valider la cohérence globale avec Claude."""
        
        contradictions_text = "\n".join([
            f"- {c['explanation']} (Sévérité: {c['severity']})"
            for c in contradictions
        ])
        
        prompt = f"""
Validez la cohérence de ce contenu:

CONTENU À VALIDER:
{content}

CONTRADICTIONS DÉTECTÉES:
{contradictions_text}

Évaluez:
1. Le contenu est-il globalement cohérent?
2. Les contradictions sont-elles résolvables?
3. Niveau de confiance dans la validation
4. Recommandations d'amélioration

Format JSON:
{{
    "is_consistent": boolean,
    "confidence": float,
    "resolvable_contradictions": boolean,
    "recommendations": ["liste", "de", "recommandations"],
    "overall_assessment": "évaluation globale"
}}
"""
        
        messages = [
            SystemMessage(content=self._get_validation_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "is_consistent": False,
                "confidence": 0.0,
                "resolvable_contradictions": False,
                "recommendations": [],
                "overall_assessment": "Failed to parse validation"
            }
    
    async def _propose_resolution(self, new_content: str, contradiction: Dict) -> Dict:
        """Proposer une résolution pour une contradiction."""
        
        prompt = f"""
Proposez une résolution pour cette contradiction:

NOUVEAU CONTENU:
{new_content}

CONTRADICTION:
Type: {contradiction['type']}
Sévérité: {contradiction['severity']}
Explication: {contradiction['explanation']}
Contenu existant: {contradiction['knowledge_content']}

Proposez une action:
1. update_existing: Mettre à jour le contenu existant
2. merge_contents: Fusionner les contenus
3. mark_deprecated: Marquer l'ancien comme obsolète
4. reject_new: Rejeter le nouveau contenu
5. manual_review: Nécessite une révision manuelle

Format JSON:
{{
    "action": "action_type",
    "target_id": "id_if_applicable",
    "updated_content": "nouveau_contenu_si_applicable",
    "reason": "justification",
    "confidence": float,
    "metadata": {{}}
}}
"""
        
        messages = [
            SystemMessage(content=self._get_resolution_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            resolution = json.loads(response.content)
            resolution["target_id"] = contradiction["knowledge_id"]
            return resolution
        except json.JSONDecodeError:
            return {
                "action": "manual_review",
                "target_id": contradiction["knowledge_id"],
                "reason": "Failed to parse resolution",
                "confidence": 0.0,
                "metadata": {}
            }
    
    def _get_contradiction_system_prompt(self) -> str:
        """Prompt système pour l'analyse de contradictions."""
        return """
Vous êtes un expert en détection de contradictions pour un système AGI.

Votre rôle est d'identifier avec précision les contradictions entre contenus:
- Contradictions factuelles: informations opposées sur les mêmes faits
- Contradictions logiques: raisonnements incompatibles
- Contradictions temporelles: informations obsolètes vs actuelles

Soyez précis et nuancé dans vos analyses.
"""
    
    def _get_validation_system_prompt(self) -> str:
        """Prompt système pour la validation de cohérence."""
        return """
Vous êtes un expert en validation de cohérence pour un système AGI.

Évaluez la cohérence globale des connaissances en tenant compte:
- La logique interne du contenu
- La compatibilité avec les connaissances existantes
- La résolvabilité des contradictions détectées
- La fiabilité des sources

Fournissez des évaluations équilibrées et constructives.
"""
    
    def _get_resolution_system_prompt(self) -> str:
        """Prompt système pour la résolution de conflits."""
        return """
Vous êtes un expert en résolution de conflits pour un système AGI.

Proposez des résolutions pragmatiques qui:
- Préservent l'intégrité des connaissances
- Minimisent la perte d'information
- Favorisent la cohérence globale
- Sont techniquement réalisables

Privilégiez les solutions qui améliorent la qualité globale du système.
"""