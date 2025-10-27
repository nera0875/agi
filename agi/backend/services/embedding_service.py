"""
Service de gestion des embeddings et recherche sémantique
Intègre Voyage AI pour les embeddings et Cohere pour le reranking
"""

import asyncio
import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import numpy as np

from services.external_services import ExternalServicesManager
from services.memory_service import MemoryService
from services.graph_service import GraphService

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service de gestion des embeddings et recherche sémantique avancée"""
    
    def __init__(
        self, 
        external_services: ExternalServicesManager,
        memory_service: MemoryService,
        graph_service: GraphService
    ):
        self.external_services = external_services
        self.memory_service = memory_service
        self.graph_service = graph_service
        
    async def initialize(self):
        """Initialise le service d'embeddings"""
        try:
            # Vérifier que les services externes sont disponibles
            await self.external_services.health_check()
            logger.info("EmbeddingService initialisé avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation d'EmbeddingService: {e}")
            raise
    
    async def semantic_search(
        self,
        user_id: UUID,
        query: str,
        search_memories: bool = True,
        search_concepts: bool = True,
        limit: int = 10,
        similarity_threshold: float = 0.7,
        use_reranking: bool = True
    ) -> Dict[str, Any]:
        """Recherche sémantique hybride dans mémoires et concepts"""
        
        try:
            results = {
                "query": query,
                "memories": [],
                "concepts": [],
                "combined_results": []
            }
            
            # Recherche dans les mémoires
            if search_memories:
                memories = await self.memory_service.search_memories(
                    user_id=user_id,
                    query=query,
                    limit=limit,
                    similarity_threshold=similarity_threshold
                )
                results["memories"] = memories
            
            # Recherche dans les concepts
            if search_concepts:
                concepts = await self.graph_service.find_similar_concepts(
                    user_id=user_id,
                    query=query,
                    limit=limit
                )
                results["concepts"] = concepts
            
            # Combiner et reranker les résultats si demandé
            if use_reranking and (results["memories"] or results["concepts"]):
                combined_results = await self._combine_and_rerank_results(
                    query=query,
                    memories=results["memories"],
                    concepts=results["concepts"],
                    limit=limit
                )
                results["combined_results"] = combined_results
            
            logger.info(f"Recherche sémantique terminée: {len(results['memories'])} mémoires, {len(results['concepts'])} concepts")
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche sémantique: {e}")
            raise
    
    async def find_related_content(
        self,
        user_id: UUID,
        content: str,
        context_window: int = 5,
        include_graph_neighbors: bool = True
    ) -> Dict[str, Any]:
        """Trouve du contenu lié basé sur les embeddings et le graphe"""
        
        try:
            # Générer l'embedding du contenu
            content_embedding = await self.external_services.voyage_ai.get_embedding(content)
            
            # Rechercher des mémoires similaires
            similar_memories = await self.memory_service.search_memories(
                user_id=user_id,
                query=content,
                limit=context_window
            )
            
            related_content = {
                "source_content": content,
                "similar_memories": similar_memories,
                "related_concepts": [],
                "graph_neighbors": []
            }
            
            # Extraire les concepts du contenu et trouver des relations
            if include_graph_neighbors and similar_memories:
                # Utiliser les concepts des mémoires similaires pour explorer le graphe
                for memory in similar_memories[:3]:  # Limiter à 3 mémoires
                    # Rechercher des concepts liés dans le graphe
                    concepts = await self.graph_service.find_similar_concepts(
                        user_id=user_id,
                        query=memory["content"][:100],  # Utiliser les premiers 100 caractères
                        limit=5
                    )
                    
                    for concept in concepts:
                        # Trouver les voisins de ce concept
                        neighbors = await self.graph_service.get_concept_neighbors(
                            concept_id=concept["id"],
                            max_depth=2,
                            min_strength=0.3
                        )
                        
                        related_content["graph_neighbors"].extend(neighbors)
            
            # Déduplication des voisins du graphe
            seen_ids = set()
            unique_neighbors = []
            for neighbor in related_content["graph_neighbors"]:
                concept_id = neighbor["concept"]["id"]
                if concept_id not in seen_ids:
                    seen_ids.add(concept_id)
                    unique_neighbors.append(neighbor)
            
            related_content["graph_neighbors"] = unique_neighbors[:10]  # Limiter à 10
            
            logger.info(f"Trouvé du contenu lié: {len(similar_memories)} mémoires, {len(unique_neighbors)} voisins")
            return related_content
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de contenu lié: {e}")
            raise
    
    async def extract_and_link_concepts(
        self,
        user_id: UUID,
        memory_id: UUID,
        content: str,
        auto_create_concepts: bool = True
    ) -> List[Dict[str, Any]]:
        """Extrait des concepts du contenu et les lie à la mémoire"""
        
        try:
            # Utiliser Claude pour extraire des concepts du contenu
            extraction_prompt = f"""
            Analyse le texte suivant et extrait les concepts clés (personnes, lieux, idées, objets, compétences, etc.).
            Pour chaque concept, fournis:
            - name: le nom du concept
            - type: le type (PERSON, PLACE, IDEA, OBJECT, SKILL, EVENT, etc.)
            - description: une brève description
            - importance: un score de 0.0 à 1.0
            
            Texte à analyser:
            {content}
            
            Réponds uniquement avec un JSON valide contenant une liste de concepts.
            """
            
            # Générer la réponse avec Claude
            response = await self.external_services.anthropic.generate_completion(
                messages=[{"role": "user", "content": extraction_prompt}],
                max_tokens=1000
            )
            
            # Parser la réponse JSON (simplifiée pour cet exemple)
            import json
            try:
                concepts_data = json.loads(response)
                if not isinstance(concepts_data, list):
                    concepts_data = concepts_data.get("concepts", [])
            except json.JSONDecodeError:
                logger.warning("Impossible de parser la réponse JSON pour l'extraction de concepts")
                concepts_data = []
            
            extracted_concepts = []
            
            # Créer ou mettre à jour les concepts dans le graphe
            for concept_data in concepts_data:
                if auto_create_concepts:
                    concept = await self.graph_service.create_concept(
                        user_id=user_id,
                        name=concept_data.get("name", ""),
                        concept_type=concept_data.get("type", "UNKNOWN"),
                        description=concept_data.get("description", ""),
                        importance=concept_data.get("importance", 0.5)
                    )
                    
                    if concept:
                        extracted_concepts.append({
                            "id": concept["id"],
                            "name": concept["name"],
                            "type": concept["type"],
                            "relevance": concept_data.get("importance", 0.5)
                        })
            
            # Lier les concepts à la mémoire
            if extracted_concepts:
                await self.graph_service.link_memory_to_concepts(
                    memory_id=memory_id,
                    user_id=user_id,
                    concepts=extracted_concepts
                )
            
            logger.info(f"Extrait et lié {len(extracted_concepts)} concepts à la mémoire {memory_id}")
            return extracted_concepts
            
        except Exception as e:
            logger.error(f"Erreur lors de l'extraction de concepts: {e}")
            return []
    
    async def calculate_content_similarity(
        self,
        content1: str,
        content2: str
    ) -> float:
        """Calcule la similarité entre deux contenus"""
        
        try:
            # Générer les embeddings
            embedding1 = await self.external_services.voyage_ai.get_embedding(content1)
            embedding2 = await self.external_services.voyage_ai.get_embedding(content2)
            
            # Calculer la similarité cosinus
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de similarité: {e}")
            return 0.0
    
    async def generate_content_summary(
        self,
        content: str,
        max_length: int = 200
    ) -> str:
        """Génère un résumé du contenu"""
        
        try:
            summary_prompt = f"""
            Résume le texte suivant en maximum {max_length} caractères, en gardant les informations les plus importantes:
            
            {content}
            
            Résumé:
            """
            
            summary = await self.external_services.anthropic.generate_completion(
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=100
            )
            
            # Nettoyer et limiter la longueur
            summary = summary.strip()
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération de résumé: {e}")
            return content[:max_length-3] + "..." if len(content) > max_length else content
    
    async def _combine_and_rerank_results(
        self,
        query: str,
        memories: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Combine et reranke les résultats de mémoires et concepts"""
        
        try:
            # Préparer les documents pour le reranking
            documents = []
            
            # Ajouter les mémoires
            for memory in memories:
                documents.append({
                    "text": memory["content"],
                    "type": "memory",
                    "data": memory,
                    "original_score": memory.get("similarity", 0.0)
                })
            
            # Ajouter les concepts
            for concept in concepts:
                concept_text = f"{concept['name']}: {concept.get('description', '')}"
                documents.append({
                    "text": concept_text,
                    "type": "concept", 
                    "data": concept,
                    "original_score": concept.get("importance", 0.0)
                })
            
            if not documents:
                return []
            
            # Utiliser Cohere pour le reranking
            texts = [doc["text"] for doc in documents]
            reranked_results = await self.external_services.cohere.rerank_documents(
                query=query,
                documents=texts,
                top_k=min(limit, len(documents))
            )
            
            # Combiner les résultats rerankés avec les données originales
            combined_results = []
            for result in reranked_results:
                original_doc = documents[result["index"]]
                combined_results.append({
                    "type": original_doc["type"],
                    "data": original_doc["data"],
                    "original_score": original_doc["original_score"],
                    "rerank_score": result["relevance_score"],
                    "combined_score": (original_doc["original_score"] + result["relevance_score"]) / 2
                })
            
            # Trier par score combiné
            combined_results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            logger.info(f"Reranking terminé: {len(combined_results)} résultats combinés")
            return combined_results
            
        except Exception as e:
            logger.error(f"Erreur lors du reranking: {e}")
            # Fallback: retourner les résultats originaux sans reranking
            fallback_results = []
            
            for memory in memories:
                fallback_results.append({
                    "type": "memory",
                    "data": memory,
                    "original_score": memory.get("similarity", 0.0),
                    "rerank_score": 0.0,
                    "combined_score": memory.get("similarity", 0.0)
                })
            
            for concept in concepts:
                fallback_results.append({
                    "type": "concept",
                    "data": concept,
                    "original_score": concept.get("importance", 0.0),
                    "rerank_score": 0.0,
                    "combined_score": concept.get("importance", 0.0)
                })
            
            fallback_results.sort(key=lambda x: x["combined_score"], reverse=True)
            return fallback_results[:limit]
    
    async def health_check(self) -> Dict[str, Any]:
        """Vérifie la santé du service d'embeddings"""
        
        try:
            # Vérifier les services externes
            external_health = await self.external_services.health_check()
            
            # Test simple d'embedding
            test_embedding = await self.external_services.voyage_ai.get_embedding("test")
            
            if test_embedding and len(test_embedding) > 0:
                return {
                    "status": "healthy",
                    "external_services": external_health,
                    "embedding_dimension": len(test_embedding),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy", 
                    "error": "Test d'embedding échoué",
                    "external_services": external_health
                }
                
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}