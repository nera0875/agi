"""
Services externes pour l'intégration avec les APIs d'IA.
Gestion des clients Voyage AI, Cohere, et Anthropic Claude.
"""

import asyncio
from typing import List, Dict, Any, Optional
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()


class VoyageAIService:
    """Service pour l'intégration avec Voyage AI (embeddings)."""
    
    def __init__(self):
        self.api_key = settings.voyage_api_key
        self.base_url = "https://api.voyageai.com/v1"
        self.model = "voyage-large-2"
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_embeddings(
        self, 
        texts: List[str], 
        input_type: str = "document"
    ) -> List[List[float]]:
        """
        Créer des embeddings pour une liste de textes.
        
        Args:
            texts: Liste des textes à encoder
            input_type: Type d'input ("document" ou "query")
            
        Returns:
            Liste des vecteurs d'embeddings
        """
        if not self.api_key:
            raise ValueError("VOYAGE_API_KEY non configurée")
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/embeddings",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "input": texts,
                        "model": self.model,
                        "input_type": input_type
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                embeddings = [item["embedding"] for item in data["data"]]
                
                logger.info(
                    "Embeddings créés avec succès",
                    count=len(embeddings),
                    model=self.model
                )
                
                return embeddings
                
            except httpx.HTTPError as e:
                logger.error("Erreur lors de la création des embeddings", error=str(e))
                raise
                
    async def create_single_embedding(
        self, 
        text: str, 
        input_type: str = "document"
    ) -> List[float]:
        """Créer un embedding pour un seul texte."""
        embeddings = await self.create_embeddings([text], input_type)
        return embeddings[0]


class CohereService:
    """Service pour l'intégration avec Cohere (reranking)."""
    
    def __init__(self):
        self.api_key = settings.cohere_api_key
        self.base_url = "https://api.cohere.ai/v1"
        self.model = "rerank-multilingual-v3.0"
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def rerank_documents(
        self,
        query: str,
        documents: List[str],
        top_k: int = 10,
        return_documents: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Reranker des documents par rapport à une requête.
        
        Args:
            query: Requête de recherche
            documents: Liste des documents à reranker
            top_k: Nombre de documents à retourner
            return_documents: Inclure le texte des documents
            
        Returns:
            Liste des documents rerankés avec scores
        """
        if not self.api_key:
            raise ValueError("COHERE_API_KEY non configurée")
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/rerank",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "query": query,
                        "documents": documents,
                        "top_k": top_k,
                        "return_documents": return_documents
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                results = data["results"]
                
                logger.info(
                    "Documents rerankés avec succès",
                    query_length=len(query),
                    documents_count=len(documents),
                    results_count=len(results)
                )
                
                return results
                
            except httpx.HTTPError as e:
                logger.error("Erreur lors du reranking", error=str(e))
                raise


class AnthropicService:
    """Service pour l'intégration avec Anthropic Claude."""
    
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-sonnet-20240229"
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Générer une completion avec Claude.
        
        Args:
            messages: Liste des messages de conversation
            max_tokens: Nombre maximum de tokens
            temperature: Température de génération
            system_prompt: Prompt système optionnel
            
        Returns:
            Réponse de Claude avec métadonnées
        """
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY non configurée")
            
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                
                data = response.json()
                
                logger.info(
                    "Completion générée avec succès",
                    model=self.model,
                    input_tokens=data.get("usage", {}).get("input_tokens", 0),
                    output_tokens=data.get("usage", {}).get("output_tokens", 0)
                )
                
                return data
                
            except httpx.HTTPError as e:
                logger.error("Erreur lors de la génération", error=str(e))
                raise
                
    async def generate_streaming_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None
    ):
        """Générer une completion en streaming."""
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY non configurée")
            
        async with httpx.AsyncClient() as client:
            try:
                payload = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages,
                    "stream": True
                }
                
                if system_prompt:
                    payload["system"] = system_prompt
                
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json=payload,
                    timeout=60.0
                ) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix
                            if data.strip() == "[DONE]":
                                break
                            try:
                                yield data
                            except Exception as e:
                                logger.error("Erreur parsing streaming data", error=str(e))
                                continue
                                
            except httpx.HTTPError as e:
                logger.error("Erreur lors du streaming", error=str(e))
                raise


class ExternalServicesManager:
    """Gestionnaire centralisé pour tous les services externes."""
    
    def __init__(self):
        self.voyage = VoyageAIService()
        self.cohere = CohereService()
        self.anthropic = AnthropicService()
        
    async def health_check(self) -> Dict[str, bool]:
        """Vérifier la santé de tous les services externes."""
        results = {}
        
        # Test Voyage AI
        try:
            await self.voyage.create_single_embedding("test")
            results["voyage_ai"] = True
        except Exception:
            results["voyage_ai"] = False
            
        # Test Cohere
        try:
            await self.cohere.rerank_documents("test", ["document test"], top_k=1)
            results["cohere"] = True
        except Exception:
            results["cohere"] = False
            
        # Test Anthropic
        try:
            await self.anthropic.generate_completion(
                [{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            results["anthropic"] = True
        except Exception:
            results["anthropic"] = False
            
        return results


# Instance globale
external_services = ExternalServicesManager()