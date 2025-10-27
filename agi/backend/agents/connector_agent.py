"""
ConnectorAgent - Gestion du graphe de connaissances et des connexions.

Responsabilités:
- Créer et maintenir les connexions dans le graphe de connaissances
- Identifier les relations manquantes entre entités
- Optimiser la structure du graphe pour les requêtes
- Enrichir les métadonnées des relations existantes
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
import json
from collections import defaultdict, deque

from .base_agent import BaseAgent, AgentConfig, AgentState
from ..services.memory_service import MemoryService
from ..services.embedding_service import EmbeddingService
from ..services.graph_service import GraphService
import structlog

logger = structlog.get_logger(__name__)


class Connection:
    """Représentation d'une connexion dans le graphe."""
    def __init__(self, source_id: str, target_id: str, connection_type: str,
                 strength: float, metadata: Dict[str, Any] = None):
        self.source_id = source_id
        self.target_id = target_id
        self.connection_type = connection_type
        self.strength = strength
        self.metadata = metadata or {}


class GraphAnalysis:
    """Résultat d'une analyse de graphe."""
    def __init__(self):
        self.isolated_nodes = []
        self.weak_connections = []
        self.missing_connections = []
        self.redundant_connections = []
        self.centrality_scores = {}
        self.clusters = []


class ConnectorAgent(BaseAgent):
    """
    Agent responsable de la gestion du graphe de connaissances.
    
    Utilise des algorithmes de graphe et Claude pour optimiser
    la structure et les connexions du graphe de connaissances.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Services requis
        self.memory_service: MemoryService = services.get("memory_service")
        self.embedding_service: EmbeddingService = services.get("embedding_service")
        self.graph_service: GraphService = services.get("graph_service")
        
        # Claude LLM pour analyse sémantique
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.1,
            max_tokens=4000
        )
        
        # Paramètres de connexion
        self.min_connection_strength = 0.3
        self.max_connections_per_node = 20
        self.similarity_threshold = 0.7
        self.centrality_threshold = 0.1
        
        # Types de connexions supportés
        self.connection_types = {
            "semantic": "Relation sémantique",
            "temporal": "Relation temporelle",
            "causal": "Relation causale",
            "hierarchical": "Relation hiérarchique",
            "associative": "Relation associative",
            "functional": "Relation fonctionnelle"
        }
        
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour la gestion des connexions."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("analyze_graph_structure", self._analyze_graph_structure)
        workflow.add_node("identify_missing_connections", self._identify_missing_connections)
        workflow.add_node("create_new_connections", self._create_new_connections)
        workflow.add_node("optimize_existing_connections", self._optimize_existing_connections)
        workflow.add_node("update_graph_metadata", self._update_graph_metadata)
        
        # Définir les transitions
        workflow.set_entry_point("analyze_graph_structure")
        workflow.add_edge("analyze_graph_structure", "identify_missing_connections")
        workflow.add_edge("identify_missing_connections", "create_new_connections")
        workflow.add_edge("create_new_connections", "optimize_existing_connections")
        workflow.add_edge("optimize_existing_connections", "update_graph_metadata")
        workflow.add_edge("update_graph_metadata", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour la gestion des connexions."""
        return await self.run(state)
    
    async def _analyze_graph_structure(self, state: AgentState) -> AgentState:
        """Analyser la structure actuelle du graphe."""
        self._log_step("analyze_graph_structure", state)
        state = self._increment_step(state)
        
        try:
            # Récupérer la structure du graphe
            graph_stats = await self.graph_service.get_graph_statistics()
            
            # Analyser les nœuds isolés
            isolated_nodes = await self.graph_service.find_isolated_nodes()
            
            # Calculer les scores de centralité
            centrality_scores = await self.graph_service.calculate_centrality_scores()
            
            # Identifier les clusters
            clusters = await self.graph_service.detect_communities()
            
            # Créer l'analyse
            analysis = GraphAnalysis()
            analysis.isolated_nodes = isolated_nodes
            analysis.centrality_scores = centrality_scores
            analysis.clusters = clusters
            
            state["context"]["graph_analysis"] = analysis
            state["context"]["graph_stats"] = graph_stats
            
            self.logger.info("Graph structure analysis completed",
                           total_nodes=graph_stats.get("node_count", 0),
                           total_edges=graph_stats.get("edge_count", 0),
                           isolated_nodes=len(isolated_nodes),
                           clusters=len(clusters))
            
        except Exception as e:
            state["error"] = f"Graph structure analysis failed: {str(e)}"
            self.logger.error("Graph structure analysis failed", error=str(e))
        
        return state
    
    async def _identify_missing_connections(self, state: AgentState) -> AgentState:
        """Identifier les connexions manquantes potentielles."""
        self._log_step("identify_missing_connections", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            analysis = state["context"]["graph_analysis"]
            
            # Identifier les connexions manquantes par similarité sémantique
            semantic_connections = await self._find_semantic_connections()
            
            # Identifier les connexions manquantes par analyse temporelle
            temporal_connections = await self._find_temporal_connections()
            
            # Identifier les connexions manquantes par analyse causale
            causal_connections = await self._find_causal_connections()
            
            # Analyser avec Claude pour des connexions plus complexes
            claude_connections = await self._find_connections_with_claude()
            
            all_missing_connections = (
                semantic_connections + 
                temporal_connections + 
                causal_connections + 
                claude_connections
            )
            
            # Filtrer et prioriser les connexions
            prioritized_connections = self._prioritize_connections(all_missing_connections)
            
            state["context"]["missing_connections"] = prioritized_connections
            state["context"]["missing_connection_count"] = len(prioritized_connections)
            
            self.logger.info("Missing connection identification completed",
                           semantic=len(semantic_connections),
                           temporal=len(temporal_connections),
                           causal=len(causal_connections),
                           claude=len(claude_connections),
                           total_prioritized=len(prioritized_connections))
            
        except Exception as e:
            state["error"] = f"Missing connection identification failed: {str(e)}"
            self.logger.error("Missing connection identification failed", error=str(e))
        
        return state
    
    async def _create_new_connections(self, state: AgentState) -> AgentState:
        """Créer les nouvelles connexions identifiées."""
        self._log_step("create_new_connections", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            missing_connections = state["context"].get("missing_connections", [])
            created_count = 0
            
            for connection in missing_connections:
                # Vérifier que la connexion n'existe pas déjà
                exists = await self.graph_service.connection_exists(
                    connection.source_id, 
                    connection.target_id,
                    connection.connection_type
                )
                
                if not exists and connection.strength >= self.min_connection_strength:
                    # Créer la connexion
                    await self.graph_service.create_relationship(
                        source_id=connection.source_id,
                        target_id=connection.target_id,
                        relationship_type=connection.connection_type,
                        properties={
                            "strength": connection.strength,
                            "created_by": "ConnectorAgent",
                            "metadata": connection.metadata
                        }
                    )
                    created_count += 1
            
            state["context"]["created_connections"] = created_count
            
            self.logger.info("New connection creation completed",
                           created_count=created_count)
            
        except Exception as e:
            state["error"] = f"New connection creation failed: {str(e)}"
            self.logger.error("New connection creation failed", error=str(e))
        
        return state
    
    async def _optimize_existing_connections(self, state: AgentState) -> AgentState:
        """Optimiser les connexions existantes."""
        self._log_step("optimize_existing_connections", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Récupérer toutes les connexions existantes
            existing_connections = await self.graph_service.get_all_relationships()
            
            optimized_count = 0
            removed_count = 0
            
            for connection in existing_connections:
                # Recalculer la force de la connexion
                new_strength = await self._recalculate_connection_strength(connection)
                
                if new_strength < self.min_connection_strength:
                    # Supprimer les connexions faibles
                    await self.graph_service.remove_relationship(
                        connection["id"]
                    )
                    removed_count += 1
                elif abs(new_strength - connection.get("strength", 0)) > 0.1:
                    # Mettre à jour la force de la connexion
                    await self.graph_service.update_relationship_properties(
                        connection["id"],
                        {"strength": new_strength}
                    )
                    optimized_count += 1
            
            state["context"]["optimized_connections"] = optimized_count
            state["context"]["removed_connections"] = removed_count
            
            self.logger.info("Connection optimization completed",
                           optimized=optimized_count,
                           removed=removed_count)
            
        except Exception as e:
            state["error"] = f"Connection optimization failed: {str(e)}"
            self.logger.error("Connection optimization failed", error=str(e))
        
        return state
    
    async def _update_graph_metadata(self, state: AgentState) -> AgentState:
        """Mettre à jour les métadonnées du graphe."""
        self._log_step("update_graph_metadata", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            # Recalculer les statistiques du graphe
            new_stats = await self.graph_service.get_graph_statistics()
            
            # Mettre à jour les scores de centralité
            await self.graph_service.update_centrality_scores()
            
            # Mettre à jour les métadonnées des nœuds
            await self.graph_service.update_node_metadata()
            
            state["context"]["final_graph_stats"] = new_stats
            state["context"]["graph_optimization_complete"] = True
            
            self.logger.info("Graph metadata update completed",
                           final_nodes=new_stats.get("node_count", 0),
                           final_edges=new_stats.get("edge_count", 0))
            
        except Exception as e:
            state["error"] = f"Graph metadata update failed: {str(e)}"
            self.logger.error("Graph metadata update failed", error=str(e))
        
        return state
    
    async def _find_semantic_connections(self) -> List[Connection]:
        """Trouver des connexions basées sur la similarité sémantique."""
        connections = []
        
        try:
            # Récupérer tous les nœuds avec leurs embeddings
            nodes_with_embeddings = await self.graph_service.get_nodes_with_embeddings()
            
            # Comparer tous les pairs de nœuds
            for i, node1 in enumerate(nodes_with_embeddings):
                for node2 in nodes_with_embeddings[i+1:]:
                    if node1["id"] == node2["id"]:
                        continue
                    
                    # Calculer la similarité sémantique
                    similarity = self.embedding_service.cosine_similarity(
                        node1["embedding"], node2["embedding"]
                    )
                    
                    if similarity >= self.similarity_threshold:
                        # Vérifier qu'une connexion n'existe pas déjà
                        exists = await self.graph_service.connection_exists(
                            node1["id"], node2["id"], "semantic"
                        )
                        
                        if not exists:
                            connections.append(Connection(
                                source_id=node1["id"],
                                target_id=node2["id"],
                                connection_type="semantic",
                                strength=similarity,
                                metadata={
                                    "similarity_score": similarity,
                                    "detection_method": "embedding_similarity"
                                }
                            ))
            
        except Exception as e:
            self.logger.error("Semantic connection finding failed", error=str(e))
        
        return connections
    
    async def _find_temporal_connections(self) -> List[Connection]:
        """Trouver des connexions basées sur la proximité temporelle."""
        connections = []
        
        try:
            # Récupérer les nœuds avec timestamps
            temporal_nodes = await self.graph_service.get_nodes_with_timestamps()
            
            # Trier par timestamp
            temporal_nodes.sort(key=lambda x: x.get("timestamp", 0))
            
            # Identifier les séquences temporelles
            for i, node1 in enumerate(temporal_nodes[:-1]):
                node2 = temporal_nodes[i + 1]
                
                # Calculer la proximité temporelle
                time_diff = abs(node2.get("timestamp", 0) - node1.get("timestamp", 0))
                
                # Si les nœuds sont proches temporellement (ex: < 1 heure)
                if time_diff < 3600:  # 1 heure en secondes
                    strength = max(0.1, 1.0 - (time_diff / 3600))
                    
                    connections.append(Connection(
                        source_id=node1["id"],
                        target_id=node2["id"],
                        connection_type="temporal",
                        strength=strength,
                        metadata={
                            "time_difference": time_diff,
                            "detection_method": "temporal_proximity"
                        }
                    ))
            
        except Exception as e:
            self.logger.error("Temporal connection finding failed", error=str(e))
        
        return connections
    
    async def _find_causal_connections(self) -> List[Connection]:
        """Trouver des connexions causales potentielles."""
        connections = []
        
        try:
            # Récupérer les nœuds avec des indicateurs causaux
            causal_indicators = ["because", "due to", "caused by", "results in", "leads to"]
            
            nodes_with_content = await self.graph_service.get_nodes_with_content()
            
            for node in nodes_with_content:
                content = node.get("content", "").lower()
                
                # Chercher des indicateurs causaux
                for indicator in causal_indicators:
                    if indicator in content:
                        # Analyser le contexte pour identifier les entités liées
                        related_entities = await self._extract_causal_entities(
                            content, indicator
                        )
                        
                        for entity_id in related_entities:
                            if entity_id != node["id"]:
                                connections.append(Connection(
                                    source_id=node["id"],
                                    target_id=entity_id,
                                    connection_type="causal",
                                    strength=0.6,  # Force modérée pour les relations causales détectées
                                    metadata={
                                        "causal_indicator": indicator,
                                        "detection_method": "causal_pattern_matching"
                                    }
                                ))
            
        except Exception as e:
            self.logger.error("Causal connection finding failed", error=str(e))
        
        return connections
    
    async def _find_connections_with_claude(self) -> List[Connection]:
        """Utiliser Claude pour identifier des connexions complexes."""
        connections = []
        
        try:
            # Récupérer un échantillon de nœuds pour analyse
            sample_nodes = await self.graph_service.get_sample_nodes(limit=20)
            
            if len(sample_nodes) < 2:
                return connections
            
            # Préparer les données pour Claude
            nodes_description = self._prepare_nodes_for_claude(sample_nodes)
            
            # Analyser avec Claude
            claude_analysis = await self._analyze_connections_with_claude(nodes_description)
            
            # Parser les résultats
            for connection_data in claude_analysis.get("connections", []):
                if (connection_data.get("confidence", 0) >= 0.5 and
                    connection_data.get("source_id") and
                    connection_data.get("target_id")):
                    
                    connections.append(Connection(
                        source_id=connection_data["source_id"],
                        target_id=connection_data["target_id"],
                        connection_type=connection_data.get("type", "associative"),
                        strength=connection_data.get("confidence", 0.5),
                        metadata={
                            "reasoning": connection_data.get("reasoning", ""),
                            "detection_method": "claude_analysis"
                        }
                    ))
            
        except Exception as e:
            self.logger.error("Claude connection finding failed", error=str(e))
        
        return connections
    
    def _prioritize_connections(self, connections: List[Connection]) -> List[Connection]:
        """Prioriser les connexions par importance."""
        # Trier par force de connexion et type
        type_priority = {
            "causal": 1.0,
            "hierarchical": 0.9,
            "semantic": 0.8,
            "temporal": 0.7,
            "associative": 0.6,
            "functional": 0.5
        }
        
        def connection_score(conn):
            type_score = type_priority.get(conn.connection_type, 0.5)
            return conn.strength * type_score
        
        sorted_connections = sorted(connections, key=connection_score, reverse=True)
        
        # Limiter le nombre de connexions pour éviter la surcharge
        return sorted_connections[:100]
    
    async def _recalculate_connection_strength(self, connection: Dict) -> float:
        """Recalculer la force d'une connexion existante."""
        try:
            source_id = connection.get("source_id")
            target_id = connection.get("target_id")
            connection_type = connection.get("type")
            
            if connection_type == "semantic":
                # Recalculer la similarité sémantique
                source_embedding = await self.graph_service.get_node_embedding(source_id)
                target_embedding = await self.graph_service.get_node_embedding(target_id)
                
                if source_embedding and target_embedding:
                    return self.embedding_service.cosine_similarity(
                        source_embedding, target_embedding
                    )
            
            elif connection_type == "temporal":
                # Recalculer la proximité temporelle
                source_timestamp = await self.graph_service.get_node_timestamp(source_id)
                target_timestamp = await self.graph_service.get_node_timestamp(target_id)
                
                if source_timestamp and target_timestamp:
                    time_diff = abs(target_timestamp - source_timestamp)
                    return max(0.1, 1.0 - (time_diff / 3600))
            
            # Pour les autres types, garder la force actuelle
            return connection.get("strength", 0.5)
            
        except Exception as e:
            self.logger.error("Connection strength recalculation failed", 
                            connection_id=connection.get("id"), error=str(e))
            return connection.get("strength", 0.5)
    
    async def _extract_causal_entities(self, content: str, indicator: str) -> List[str]:
        """Extraire les entités liées causalement dans un texte."""
        # Implémentation simplifiée - dans un vrai système, 
        # on utiliserait des techniques NLP plus avancées
        entities = []
        
        try:
            # Chercher les entités mentionnées près de l'indicateur causal
            indicator_pos = content.find(indicator)
            if indicator_pos != -1:
                # Extraire le contexte autour de l'indicateur
                context_start = max(0, indicator_pos - 100)
                context_end = min(len(content), indicator_pos + 100)
                context = content[context_start:context_end]
                
                # Rechercher des entités connues dans ce contexte
                known_entities = await self.graph_service.get_entity_names()
                
                for entity in known_entities:
                    if entity.lower() in context.lower():
                        entity_id = await self.graph_service.get_entity_id_by_name(entity)
                        if entity_id:
                            entities.append(entity_id)
            
        except Exception as e:
            self.logger.error("Causal entity extraction failed", error=str(e))
        
        return entities
    
    def _prepare_nodes_for_claude(self, nodes: List[Dict]) -> str:
        """Préparer la description des nœuds pour Claude."""
        descriptions = []
        
        for node in nodes:
            desc = f"ID: {node['id']}\n"
            desc += f"Contenu: {node.get('content', '')[:200]}...\n"
            desc += f"Type: {node.get('type', 'unknown')}\n"
            desc += f"Métadonnées: {node.get('metadata', {})}\n"
            descriptions.append(desc)
        
        return "\n---\n".join(descriptions)
    
    async def _analyze_connections_with_claude(self, nodes_description: str) -> Dict:
        """Analyser les connexions potentielles avec Claude."""
        
        prompt = f"""
Analysez ces nœuds de graphe de connaissances et identifiez les connexions potentielles:

NŒUDS:
{nodes_description}

Identifiez les connexions logiques entre ces nœuds en considérant:
1. Relations sémantiques (concepts similaires ou liés)
2. Relations hiérarchiques (généralisation/spécialisation)
3. Relations causales (cause-effet)
4. Relations fonctionnelles (processus liés)
5. Relations associatives (fréquemment mentionnés ensemble)

Format JSON:
{{
    "connections": [
        {{
            "source_id": "id_source",
            "target_id": "id_target",
            "type": "semantic|hierarchical|causal|functional|associative",
            "confidence": float,
            "reasoning": "explication de la connexion"
        }}
    ]
}}
"""
        
        messages = [
            SystemMessage(content=self._get_connection_analysis_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse Claude connection analysis")
            return {"connections": []}
    
    def _get_connection_analysis_system_prompt(self) -> str:
        """Prompt système pour l'analyse de connexions."""
        return """
Vous êtes un expert en analyse de graphes de connaissances pour un système AGI.

Votre rôle est d'identifier des connexions significatives entre nœuds:
- Analysez le contenu sémantique pour identifier les relations
- Considérez les hiérarchies conceptuelles
- Identifiez les relations causales et fonctionnelles
- Évaluez la force et la pertinence de chaque connexion

Privilégiez la qualité à la quantité et justifiez chaque connexion proposée.
"""