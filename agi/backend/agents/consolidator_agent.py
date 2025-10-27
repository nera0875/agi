"""
ConsolidatorAgent - Consolidation mémoire L2→L3 avec Claude.

Responsabilités:
- Analyser les données de mémoire L2 (court terme)
- Identifier les patterns récurrents et informations importantes
- Consolider vers la mémoire L3 (long terme) via Claude
- Maintenir la cohérence des connaissances consolidées
"""

from typing import Any, Dict, List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor

from .base_agent import BaseAgent, AgentConfig, AgentState
from ..services.memory_service import MemoryService
from ..services.embedding_service import EmbeddingService
import structlog

logger = structlog.get_logger(__name__)


class ConsolidatorAgent(BaseAgent):
    """
    Agent responsable de la consolidation mémoire L2→L3.
    
    Utilise Claude pour analyser et consolider les informations
    de la mémoire court terme vers la mémoire long terme.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Services requis
        self.memory_service: MemoryService = services.get("memory_service")
        self.embedding_service: EmbeddingService = services.get("embedding_service")
        
        # Claude LLM pour consolidation
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Seuils de consolidation
        self.consolidation_threshold = 5  # Nombre minimum d'occurrences
        self.similarity_threshold = 0.85  # Seuil de similarité pour regroupement
        
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour la consolidation."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("analyze_l2_memory", self._analyze_l2_memory)
        workflow.add_node("identify_patterns", self._identify_patterns)
        workflow.add_node("consolidate_with_claude", self._consolidate_with_claude)
        workflow.add_node("store_l3_memory", self._store_l3_memory)
        workflow.add_node("cleanup_l2", self._cleanup_l2)
        
        # Définir les transitions
        workflow.set_entry_point("analyze_l2_memory")
        workflow.add_edge("analyze_l2_memory", "identify_patterns")
        workflow.add_edge("identify_patterns", "consolidate_with_claude")
        workflow.add_edge("consolidate_with_claude", "store_l3_memory")
        workflow.add_edge("store_l3_memory", "cleanup_l2")
        workflow.add_edge("cleanup_l2", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour la consolidation."""
        return await self.run(state)
    
    async def _analyze_l2_memory(self, state: AgentState) -> AgentState:
        """Analyser la mémoire L2 pour identifier les candidats à la consolidation."""
        self._log_step("analyze_l2_memory", state)
        state = self._increment_step(state)
        
        try:
            # Récupérer les données L2 anciennes (ex: > 24h)
            l2_memories = await self.memory_service.get_l2_memories_for_consolidation(
                age_hours=24,
                min_access_count=2
            )
            
            state["context"]["l2_candidates"] = l2_memories
            state["context"]["candidate_count"] = len(l2_memories)
            
            self.logger.info("L2 memory analysis completed", 
                           candidate_count=len(l2_memories))
            
        except Exception as e:
            state["error"] = f"L2 analysis failed: {str(e)}"
            self.logger.error("L2 analysis failed", error=str(e))
        
        return state
    
    async def _identify_patterns(self, state: AgentState) -> AgentState:
        """Identifier les patterns et regrouper les mémoires similaires."""
        self._log_step("identify_patterns", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            l2_candidates = state["context"].get("l2_candidates", [])
            
            if not l2_candidates:
                state["context"]["patterns"] = []
                return state
            
            # Grouper par similarité sémantique
            patterns = await self._group_by_similarity(l2_candidates)
            
            # Filtrer les patterns avec suffisamment d'occurrences
            significant_patterns = [
                pattern for pattern in patterns 
                if len(pattern["memories"]) >= self.consolidation_threshold
            ]
            
            state["context"]["patterns"] = significant_patterns
            state["context"]["pattern_count"] = len(significant_patterns)
            
            self.logger.info("Pattern identification completed",
                           total_patterns=len(patterns),
                           significant_patterns=len(significant_patterns))
            
        except Exception as e:
            state["error"] = f"Pattern identification failed: {str(e)}"
            self.logger.error("Pattern identification failed", error=str(e))
        
        return state
    
    async def _consolidate_with_claude(self, state: AgentState) -> AgentState:
        """Utiliser Claude pour consolider les patterns en connaissances L3."""
        self._log_step("consolidate_with_claude", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            patterns = state["context"].get("patterns", [])
            consolidated_knowledge = []
            
            for pattern in patterns:
                # Préparer le prompt pour Claude
                consolidation_prompt = self._create_consolidation_prompt(pattern)
                
                # Appeler Claude pour consolidation
                messages = [
                    SystemMessage(content=self._get_consolidation_system_prompt()),
                    HumanMessage(content=consolidation_prompt)
                ]
                
                response = await self.llm.ainvoke(messages)
                
                # Parser la réponse de Claude
                consolidated = self._parse_claude_response(response.content, pattern)
                consolidated_knowledge.append(consolidated)
            
            state["context"]["consolidated_knowledge"] = consolidated_knowledge
            
            self.logger.info("Claude consolidation completed",
                           consolidated_count=len(consolidated_knowledge))
            
        except Exception as e:
            state["error"] = f"Claude consolidation failed: {str(e)}"
            self.logger.error("Claude consolidation failed", error=str(e))
        
        return state
    
    async def _store_l3_memory(self, state: AgentState) -> AgentState:
        """Stocker les connaissances consolidées en mémoire L3."""
        self._log_step("store_l3_memory", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            consolidated_knowledge = state["context"].get("consolidated_knowledge", [])
            stored_count = 0
            
            for knowledge in consolidated_knowledge:
                # Stocker en L3 avec embeddings
                await self.memory_service.store_l3_memory(
                    content=knowledge["content"],
                    metadata=knowledge["metadata"],
                    source_l2_ids=knowledge["source_ids"]
                )
                stored_count += 1
            
            state["context"]["stored_l3_count"] = stored_count
            
            self.logger.info("L3 storage completed", stored_count=stored_count)
            
        except Exception as e:
            state["error"] = f"L3 storage failed: {str(e)}"
            self.logger.error("L3 storage failed", error=str(e))
        
        return state
    
    async def _cleanup_l2(self, state: AgentState) -> AgentState:
        """Nettoyer les mémoires L2 consolidées."""
        self._log_step("cleanup_l2", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            consolidated_knowledge = state["context"].get("consolidated_knowledge", [])
            cleaned_count = 0
            
            for knowledge in consolidated_knowledge:
                # Marquer les L2 sources comme consolidées
                await self.memory_service.mark_l2_as_consolidated(
                    l2_ids=knowledge["source_ids"]
                )
                cleaned_count += len(knowledge["source_ids"])
            
            state["context"]["cleaned_l2_count"] = cleaned_count
            
            self.logger.info("L2 cleanup completed", cleaned_count=cleaned_count)
            
        except Exception as e:
            state["error"] = f"L2 cleanup failed: {str(e)}"
            self.logger.error("L2 cleanup failed", error=str(e))
        
        return state
    
    async def _group_by_similarity(self, memories: List[Dict]) -> List[Dict]:
        """Grouper les mémoires par similarité sémantique."""
        if not memories:
            return []
        
        # Obtenir les embeddings pour toutes les mémoires
        texts = [mem["content"] for mem in memories]
        embeddings = await self.embedding_service.get_embeddings(texts)
        
        # Algorithme de clustering simple basé sur la similarité
        patterns = []
        used_indices = set()
        
        for i, memory in enumerate(memories):
            if i in used_indices:
                continue
            
            # Créer un nouveau pattern
            pattern = {
                "representative_content": memory["content"],
                "memories": [memory],
                "embedding": embeddings[i]
            }
            used_indices.add(i)
            
            # Trouver les mémoires similaires
            for j, other_memory in enumerate(memories):
                if j in used_indices or i == j:
                    continue
                
                # Calculer la similarité cosinus
                similarity = self.embedding_service.cosine_similarity(
                    embeddings[i], embeddings[j]
                )
                
                if similarity >= self.similarity_threshold:
                    pattern["memories"].append(other_memory)
                    used_indices.add(j)
            
            patterns.append(pattern)
        
        return patterns
    
    def _create_consolidation_prompt(self, pattern: Dict) -> str:
        """Créer le prompt pour Claude pour consolider un pattern."""
        memories_text = "\n".join([
            f"- {mem['content']}" for mem in pattern["memories"]
        ])
        
        return f"""
Voici un ensemble de mémoires similaires à consolider:

{memories_text}

Nombre d'occurrences: {len(pattern["memories"])}

Veuillez analyser ces mémoires et créer une connaissance consolidée qui:
1. Capture l'essence commune de ces mémoires
2. Identifie les patterns et relations importantes
3. Synthétise l'information de manière concise mais complète
4. Préserve les détails importants tout en éliminant la redondance

Format de réponse attendu:
TITRE: [Titre concis de la connaissance]
CONTENU: [Synthèse consolidée]
CONCEPTS_CLÉS: [Liste des concepts principaux]
RELATIONS: [Relations avec d'autres connaissances]
CONFIANCE: [Score de confiance 0-1]
"""
    
    def _get_consolidation_system_prompt(self) -> str:
        """Prompt système pour Claude lors de la consolidation."""
        return """
Vous êtes un expert en consolidation de connaissances pour un système AGI.

Votre rôle est de:
- Analyser des mémoires similaires et les consolider en connaissances durables
- Identifier les patterns récurrents et les relations importantes
- Créer des synthèses précises et utiles
- Maintenir la cohérence et la qualité des connaissances

Principes:
- Privilégier la précision à la quantité
- Conserver les nuances importantes
- Identifier les relations avec d'autres connaissances
- Évaluer la confiance dans la consolidation
"""
    
    def _parse_claude_response(self, response: str, pattern: Dict) -> Dict:
        """Parser la réponse de Claude pour extraire la connaissance consolidée."""
        lines = response.strip().split('\n')
        
        consolidated = {
            "content": "",
            "metadata": {
                "source_pattern_size": len(pattern["memories"]),
                "consolidation_timestamp": None,
                "confidence_score": 0.8  # Default
            },
            "source_ids": [mem["id"] for mem in pattern["memories"]]
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if line.startswith("TITRE:"):
                consolidated["metadata"]["title"] = line.replace("TITRE:", "").strip()
            elif line.startswith("CONTENU:"):
                current_section = "content"
                consolidated["content"] = line.replace("CONTENU:", "").strip()
            elif line.startswith("CONCEPTS_CLÉS:"):
                consolidated["metadata"]["key_concepts"] = line.replace("CONCEPTS_CLÉS:", "").strip()
            elif line.startswith("RELATIONS:"):
                consolidated["metadata"]["relations"] = line.replace("RELATIONS:", "").strip()
            elif line.startswith("CONFIANCE:"):
                try:
                    score = float(line.replace("CONFIANCE:", "").strip())
                    consolidated["metadata"]["confidence_score"] = score
                except ValueError:
                    pass
            elif current_section == "content" and line:
                consolidated["content"] += " " + line
        
        return consolidated