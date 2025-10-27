"""
PatternExtractorAgent - Extraction de patterns et concepts des données.

Responsabilités:
- Analyser les données pour identifier des patterns récurrents
- Extraire des concepts et relations importantes
- Classifier et catégoriser les informations
- Enrichir le graphe de connaissances avec de nouveaux patterns
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
import json
import re
from collections import Counter, defaultdict

from .base_agent import BaseAgent, AgentConfig, AgentState
from ..services.memory_service import MemoryService
from ..services.embedding_service import EmbeddingService
from ..services.graph_service import GraphService
import structlog

logger = structlog.get_logger(__name__)


class Pattern:
    """Représentation d'un pattern extrait."""
    def __init__(self, pattern_type: str, content: str, frequency: int, 
                 confidence: float, examples: List[str] = None):
        self.pattern_type = pattern_type
        self.content = content
        self.frequency = frequency
        self.confidence = confidence
        self.examples = examples or []
        self.metadata = {}


class Concept:
    """Représentation d'un concept extrait."""
    def __init__(self, name: str, definition: str, category: str,
                 related_concepts: List[str] = None, confidence: float = 0.0):
        self.name = name
        self.definition = definition
        self.category = category
        self.related_concepts = related_concepts or []
        self.confidence = confidence
        self.metadata = {}


class PatternExtractorAgent(BaseAgent):
    """
    Agent responsable de l'extraction de patterns et concepts.
    
    Utilise des techniques de NLP, d'analyse statistique et Claude
    pour identifier et extraire des patterns significatifs.
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        super().__init__(config, services)
        
        # Services requis
        self.memory_service: MemoryService = services.get("memory_service")
        self.embedding_service: EmbeddingService = services.get("embedding_service")
        self.graph_service: GraphService = services.get("graph_service")
        
        # Claude LLM pour extraction avancée
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0.2,
            max_tokens=4000
        )
        
        # Paramètres d'extraction
        self.min_pattern_frequency = 3
        self.min_concept_confidence = 0.6
        self.max_patterns_per_batch = 50
        
        # Patterns regex pour extraction basique
        self.regex_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "url": r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',
            "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
            "time": r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b',
            "phone": r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        }
        
    def _build_graph(self) -> StateGraph:
        """Construit le graphe LangGraph pour l'extraction de patterns."""
        
        workflow = StateGraph(AgentState)
        
        # Nœuds du workflow
        workflow.add_node("prepare_data", self._prepare_data)
        workflow.add_node("extract_basic_patterns", self._extract_basic_patterns)
        workflow.add_node("extract_semantic_patterns", self._extract_semantic_patterns)
        workflow.add_node("extract_concepts", self._extract_concepts)
        workflow.add_node("analyze_relationships", self._analyze_relationships)
        workflow.add_node("store_patterns", self._store_patterns)
        
        # Définir les transitions
        workflow.set_entry_point("prepare_data")
        workflow.add_edge("prepare_data", "extract_basic_patterns")
        workflow.add_edge("extract_basic_patterns", "extract_semantic_patterns")
        workflow.add_edge("extract_semantic_patterns", "extract_concepts")
        workflow.add_edge("extract_concepts", "analyze_relationships")
        workflow.add_edge("analyze_relationships", "store_patterns")
        workflow.add_edge("store_patterns", END)
        
        return workflow.compile()
    
    async def process(self, state: AgentState) -> AgentState:
        """Point d'entrée principal pour l'extraction de patterns."""
        return await self.run(state)
    
    async def _prepare_data(self, state: AgentState) -> AgentState:
        """Préparer les données pour l'extraction."""
        self._log_step("prepare_data", state)
        state = self._increment_step(state)
        
        try:
            # Récupérer les données à analyser
            data_source = state["context"].get("data_source", "recent_memories")
            batch_size = state["context"].get("batch_size", 100)
            
            if data_source == "recent_memories":
                # Récupérer les mémoires récentes
                data = await self.memory_service.get_recent_memories(
                    limit=batch_size,
                    include_l1=True,
                    include_l2=True
                )
            elif data_source == "specific_content":
                # Utiliser le contenu spécifique fourni
                data = state["context"].get("content_data", [])
            else:
                # Récupérer toutes les données disponibles
                data = await self.memory_service.get_all_memories_for_analysis()
            
            # Préprocesser les données
            processed_data = self._preprocess_data(data)
            
            state["context"]["processed_data"] = processed_data
            state["context"]["data_count"] = len(processed_data)
            
            self.logger.info("Data preparation completed",
                           data_count=len(processed_data),
                           data_source=data_source)
            
        except Exception as e:
            state["error"] = f"Data preparation failed: {str(e)}"
            self.logger.error("Data preparation failed", error=str(e))
        
        return state
    
    async def _extract_basic_patterns(self, state: AgentState) -> AgentState:
        """Extraire les patterns de base avec regex et statistiques."""
        self._log_step("extract_basic_patterns", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            processed_data = state["context"]["processed_data"]
            basic_patterns = []
            
            # Extraction avec regex
            regex_results = self._extract_regex_patterns(processed_data)
            basic_patterns.extend(regex_results)
            
            # Extraction de patterns textuels
            text_patterns = self._extract_text_patterns(processed_data)
            basic_patterns.extend(text_patterns)
            
            # Extraction de patterns numériques
            numeric_patterns = self._extract_numeric_patterns(processed_data)
            basic_patterns.extend(numeric_patterns)
            
            state["context"]["basic_patterns"] = basic_patterns
            state["context"]["basic_pattern_count"] = len(basic_patterns)
            
            self.logger.info("Basic pattern extraction completed",
                           pattern_count=len(basic_patterns))
            
        except Exception as e:
            state["error"] = f"Basic pattern extraction failed: {str(e)}"
            self.logger.error("Basic pattern extraction failed", error=str(e))
        
        return state
    
    async def _extract_semantic_patterns(self, state: AgentState) -> AgentState:
        """Extraire les patterns sémantiques avec Claude."""
        self._log_step("extract_semantic_patterns", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            processed_data = state["context"]["processed_data"]
            
            # Grouper les données par similarité sémantique
            semantic_groups = await self._group_by_semantic_similarity(processed_data)
            
            semantic_patterns = []
            
            for group in semantic_groups:
                if len(group["items"]) >= self.min_pattern_frequency:
                    # Analyser le groupe avec Claude
                    pattern_analysis = await self._analyze_semantic_group(group)
                    
                    if pattern_analysis["confidence"] >= self.min_concept_confidence:
                        semantic_patterns.append(Pattern(
                            pattern_type="semantic",
                            content=pattern_analysis["pattern_description"],
                            frequency=len(group["items"]),
                            confidence=pattern_analysis["confidence"],
                            examples=pattern_analysis["examples"]
                        ))
            
            state["context"]["semantic_patterns"] = semantic_patterns
            state["context"]["semantic_pattern_count"] = len(semantic_patterns)
            
            self.logger.info("Semantic pattern extraction completed",
                           pattern_count=len(semantic_patterns))
            
        except Exception as e:
            state["error"] = f"Semantic pattern extraction failed: {str(e)}"
            self.logger.error("Semantic pattern extraction failed", error=str(e))
        
        return state
    
    async def _extract_concepts(self, state: AgentState) -> AgentState:
        """Extraire les concepts importants."""
        self._log_step("extract_concepts", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            processed_data = state["context"]["processed_data"]
            basic_patterns = state["context"].get("basic_patterns", [])
            semantic_patterns = state["context"].get("semantic_patterns", [])
            
            # Extraire les concepts avec Claude
            concepts = await self._extract_concepts_with_claude(
                processed_data, basic_patterns, semantic_patterns
            )
            
            # Filtrer les concepts par confiance
            filtered_concepts = [
                concept for concept in concepts
                if concept.confidence >= self.min_concept_confidence
            ]
            
            state["context"]["concepts"] = filtered_concepts
            state["context"]["concept_count"] = len(filtered_concepts)
            
            self.logger.info("Concept extraction completed",
                           concept_count=len(filtered_concepts))
            
        except Exception as e:
            state["error"] = f"Concept extraction failed: {str(e)}"
            self.logger.error("Concept extraction failed", error=str(e))
        
        return state
    
    async def _analyze_relationships(self, state: AgentState) -> AgentState:
        """Analyser les relations entre patterns et concepts."""
        self._log_step("analyze_relationships", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            concepts = state["context"].get("concepts", [])
            semantic_patterns = state["context"].get("semantic_patterns", [])
            
            # Analyser les relations avec Claude
            relationships = await self._analyze_relationships_with_claude(
                concepts, semantic_patterns
            )
            
            state["context"]["relationships"] = relationships
            state["context"]["relationship_count"] = len(relationships)
            
            self.logger.info("Relationship analysis completed",
                           relationship_count=len(relationships))
            
        except Exception as e:
            state["error"] = f"Relationship analysis failed: {str(e)}"
            self.logger.error("Relationship analysis failed", error=str(e))
        
        return state
    
    async def _store_patterns(self, state: AgentState) -> AgentState:
        """Stocker les patterns et concepts extraits."""
        self._log_step("store_patterns", state)
        state = self._increment_step(state)
        
        if state.get("error"):
            return state
        
        try:
            basic_patterns = state["context"].get("basic_patterns", [])
            semantic_patterns = state["context"].get("semantic_patterns", [])
            concepts = state["context"].get("concepts", [])
            relationships = state["context"].get("relationships", [])
            
            stored_count = 0
            
            # Stocker les patterns
            for pattern in basic_patterns + semantic_patterns:
                await self.memory_service.store_pattern(
                    pattern_type=pattern.pattern_type,
                    content=pattern.content,
                    frequency=pattern.frequency,
                    confidence=pattern.confidence,
                    examples=pattern.examples
                )
                stored_count += 1
            
            # Stocker les concepts
            for concept in concepts:
                await self.memory_service.store_concept(
                    name=concept.name,
                    definition=concept.definition,
                    category=concept.category,
                    confidence=concept.confidence,
                    metadata=concept.metadata
                )
                stored_count += 1
            
            # Stocker les relations dans le graphe
            for relationship in relationships:
                await self.graph_service.create_relationship(
                    source_id=relationship["source_id"],
                    target_id=relationship["target_id"],
                    relationship_type=relationship["type"],
                    properties=relationship["properties"]
                )
            
            state["context"]["stored_count"] = stored_count
            state["context"]["extraction_complete"] = True
            
            self.logger.info("Pattern storage completed",
                           stored_count=stored_count)
            
        except Exception as e:
            state["error"] = f"Pattern storage failed: {str(e)}"
            self.logger.error("Pattern storage failed", error=str(e))
        
        return state
    
    def _preprocess_data(self, raw_data: List[Dict]) -> List[Dict]:
        """Préprocesser les données pour l'extraction."""
        processed = []
        
        for item in raw_data:
            # Nettoyer et normaliser le texte
            content = item.get("content", "")
            if not content:
                continue
            
            # Nettoyage basique
            content = re.sub(r'\s+', ' ', content)  # Normaliser les espaces
            content = content.strip()
            
            processed_item = {
                "id": item.get("id"),
                "content": content,
                "original_content": item.get("content"),
                "metadata": item.get("metadata", {}),
                "timestamp": item.get("timestamp"),
                "word_count": len(content.split()),
                "char_count": len(content)
            }
            
            processed.append(processed_item)
        
        return processed
    
    def _extract_regex_patterns(self, data: List[Dict]) -> List[Pattern]:
        """Extraire les patterns avec des expressions régulières."""
        patterns = []
        pattern_counts = defaultdict(list)
        
        for item in data:
            content = item["content"]
            
            for pattern_name, regex in self.regex_patterns.items():
                matches = re.findall(regex, content)
                for match in matches:
                    pattern_counts[pattern_name].append({
                        "match": match,
                        "source_id": item["id"],
                        "context": content
                    })
        
        # Créer les objets Pattern
        for pattern_name, matches in pattern_counts.items():
            if len(matches) >= self.min_pattern_frequency:
                patterns.append(Pattern(
                    pattern_type="regex",
                    content=f"{pattern_name}_pattern",
                    frequency=len(matches),
                    confidence=0.9,  # Haute confiance pour les regex
                    examples=[m["match"] for m in matches[:5]]
                ))
        
        return patterns
    
    def _extract_text_patterns(self, data: List[Dict]) -> List[Pattern]:
        """Extraire les patterns textuels récurrents."""
        patterns = []
        
        # Extraire les n-grammes fréquents
        all_text = " ".join([item["content"] for item in data])
        words = re.findall(r'\b\w+\b', all_text.lower())
        
        # Bigrammes
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        bigram_counts = Counter(bigrams)
        
        # Trigrammes
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]
        trigram_counts = Counter(trigrams)
        
        # Créer les patterns pour les n-grammes fréquents
        for ngram, count in bigram_counts.most_common(20):
            if count >= self.min_pattern_frequency:
                patterns.append(Pattern(
                    pattern_type="bigram",
                    content=ngram,
                    frequency=count,
                    confidence=min(0.8, count / len(data)),
                    examples=[ngram]
                ))
        
        for ngram, count in trigram_counts.most_common(10):
            if count >= self.min_pattern_frequency:
                patterns.append(Pattern(
                    pattern_type="trigram",
                    content=ngram,
                    frequency=count,
                    confidence=min(0.8, count / len(data)),
                    examples=[ngram]
                ))
        
        return patterns
    
    def _extract_numeric_patterns(self, data: List[Dict]) -> List[Pattern]:
        """Extraire les patterns numériques."""
        patterns = []
        numbers = []
        
        for item in data:
            content = item["content"]
            # Extraire tous les nombres
            found_numbers = re.findall(r'\b\d+(?:\.\d+)?\b', content)
            numbers.extend([float(n) for n in found_numbers])
        
        if numbers:
            # Analyser les distributions numériques
            number_counter = Counter(numbers)
            
            # Patterns de nombres fréquents
            for number, count in number_counter.most_common(10):
                if count >= self.min_pattern_frequency:
                    patterns.append(Pattern(
                        pattern_type="numeric",
                        content=f"frequent_number_{number}",
                        frequency=count,
                        confidence=0.7,
                        examples=[str(number)]
                    ))
        
        return patterns
    
    async def _group_by_semantic_similarity(self, data: List[Dict]) -> List[Dict]:
        """Grouper les données par similarité sémantique."""
        if not data:
            return []
        
        # Obtenir les embeddings
        texts = [item["content"] for item in data]
        embeddings = await self.embedding_service.get_embeddings(texts)
        
        # Clustering simple basé sur la similarité
        groups = []
        used_indices = set()
        similarity_threshold = 0.75
        
        for i, item in enumerate(data):
            if i in used_indices:
                continue
            
            group = {
                "representative_item": item,
                "items": [item],
                "embedding": embeddings[i]
            }
            used_indices.add(i)
            
            # Trouver les items similaires
            for j, other_item in enumerate(data):
                if j in used_indices or i == j:
                    continue
                
                similarity = self.embedding_service.cosine_similarity(
                    embeddings[i], embeddings[j]
                )
                
                if similarity >= similarity_threshold:
                    group["items"].append(other_item)
                    used_indices.add(j)
            
            if len(group["items"]) >= 2:  # Au moins 2 items pour former un groupe
                groups.append(group)
        
        return groups
    
    async def _analyze_semantic_group(self, group: Dict) -> Dict:
        """Analyser un groupe sémantique avec Claude."""
        items_text = "\n".join([
            f"- {item['content'][:200]}..." if len(item['content']) > 200 
            else f"- {item['content']}"
            for item in group["items"][:10]  # Limiter à 10 exemples
        ])
        
        prompt = f"""
Analysez ce groupe d'éléments similaires et identifiez le pattern commun:

ÉLÉMENTS DU GROUPE ({len(group['items'])} total):
{items_text}

Identifiez:
1. Le pattern ou thème commun
2. Les caractéristiques partagées
3. Le niveau de confiance dans ce pattern
4. Des exemples représentatifs

Format JSON:
{{
    "pattern_description": "description du pattern",
    "common_characteristics": ["caractéristique1", "caractéristique2"],
    "confidence": float,
    "examples": ["exemple1", "exemple2"],
    "pattern_type": "thematic|structural|functional"
}}
"""
        
        messages = [
            SystemMessage(content=self._get_pattern_analysis_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "pattern_description": "Failed to analyze pattern",
                "common_characteristics": [],
                "confidence": 0.0,
                "examples": [],
                "pattern_type": "unknown"
            }
    
    async def _extract_concepts_with_claude(self, data: List[Dict], 
                                          basic_patterns: List[Pattern],
                                          semantic_patterns: List[Pattern]) -> List[Concept]:
        """Extraire les concepts avec Claude."""
        
        # Préparer un échantillon représentatif
        sample_data = data[:20] if len(data) > 20 else data
        sample_text = "\n".join([item["content"][:300] for item in sample_data])
        
        patterns_summary = "\n".join([
            f"- {p.pattern_type}: {p.content} (fréquence: {p.frequency})"
            for p in (basic_patterns + semantic_patterns)[:10]
        ])
        
        prompt = f"""
Analysez ces données et patterns pour extraire les concepts importants:

ÉCHANTILLON DE DONNÉES:
{sample_text}

PATTERNS IDENTIFIÉS:
{patterns_summary}

Extrayez les concepts clés en identifiant:
1. Les entités principales
2. Les catégories conceptuelles
3. Les domaines de connaissance
4. Les relations conceptuelles

Format JSON:
{{
    "concepts": [
        {{
            "name": "nom_du_concept",
            "definition": "définition claire",
            "category": "catégorie",
            "confidence": float,
            "related_concepts": ["concept1", "concept2"],
            "examples": ["exemple1", "exemple2"]
        }}
    ]
}}
"""
        
        messages = [
            SystemMessage(content=self._get_concept_extraction_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result = json.loads(response.content)
            concepts = []
            
            for concept_data in result.get("concepts", []):
                concept = Concept(
                    name=concept_data["name"],
                    definition=concept_data["definition"],
                    category=concept_data["category"],
                    related_concepts=concept_data.get("related_concepts", []),
                    confidence=concept_data.get("confidence", 0.0)
                )
                concept.metadata = {
                    "examples": concept_data.get("examples", []),
                    "extraction_method": "claude_analysis"
                }
                concepts.append(concept)
            
            return concepts
            
        except json.JSONDecodeError:
            self.logger.error("Failed to parse concept extraction response")
            return []
    
    async def _analyze_relationships_with_claude(self, concepts: List[Concept],
                                               patterns: List[Pattern]) -> List[Dict]:
        """Analyser les relations avec Claude."""
        
        concepts_text = "\n".join([
            f"- {c.name}: {c.definition} (catégorie: {c.category})"
            for c in concepts[:15]
        ])
        
        patterns_text = "\n".join([
            f"- {p.content} ({p.pattern_type})"
            for p in patterns[:10]
        ])
        
        prompt = f"""
Analysez les relations entre ces concepts et patterns:

CONCEPTS:
{concepts_text}

PATTERNS:
{patterns_text}

Identifiez les relations importantes:
1. Relations hiérarchiques (parent-enfant)
2. Relations associatives (concepts liés)
3. Relations causales (cause-effet)
4. Relations temporelles (séquence)

Format JSON:
{{
    "relationships": [
        {{
            "source_name": "concept1",
            "target_name": "concept2",
            "relationship_type": "hierarchical|associative|causal|temporal",
            "strength": float,
            "description": "description de la relation"
        }}
    ]
}}
"""
        
        messages = [
            SystemMessage(content=self._get_relationship_analysis_system_prompt()),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        try:
            result = json.loads(response.content)
            relationships = []
            
            for rel_data in result.get("relationships", []):
                relationships.append({
                    "source_id": rel_data["source_name"],
                    "target_id": rel_data["target_name"],
                    "type": rel_data["relationship_type"],
                    "properties": {
                        "strength": rel_data.get("strength", 0.5),
                        "description": rel_data.get("description", ""),
                        "extraction_method": "claude_analysis"
                    }
                })
            
            return relationships
            
        except json.JSONDecodeError:
            self.logger.error("Failed to parse relationship analysis response")
            return []
    
    def _get_pattern_analysis_system_prompt(self) -> str:
        """Prompt système pour l'analyse de patterns."""
        return """
Vous êtes un expert en analyse de patterns pour un système AGI.

Votre rôle est d'identifier des patterns significatifs dans les données:
- Patterns thématiques: sujets récurrents
- Patterns structurels: formats ou structures communes
- Patterns fonctionnels: comportements ou processus similaires

Soyez précis et analytique dans vos identifications.
"""
    
    def _get_concept_extraction_system_prompt(self) -> str:
        """Prompt système pour l'extraction de concepts."""
        return """
Vous êtes un expert en extraction de concepts pour un système AGI.

Identifiez les concepts importants en vous concentrant sur:
- Entités concrètes et abstraites
- Catégories conceptuelles
- Domaines de connaissance
- Relations entre concepts

Privilégiez la qualité à la quantité et assurez-vous que chaque concept est bien défini.
"""
    
    def _get_relationship_analysis_system_prompt(self) -> str:
        """Prompt système pour l'analyse de relations."""
        return """
Vous êtes un expert en analyse de relations conceptuelles pour un système AGI.

Identifiez les relations significatives entre concepts:
- Relations hiérarchiques: généralisation/spécialisation
- Relations associatives: concepts fréquemment liés
- Relations causales: relations de cause à effet
- Relations temporelles: séquences ou processus

Évaluez la force et l'importance de chaque relation identifiée.
"""