"""
Tests pour les routes API des agents LangGraph
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from ..main import app
from ..api.routes.agents import router


class TestAgentsAPI:
    """Tests pour les routes API des agents"""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_services(self):
        """Services mockés pour les tests API"""
        return {
            "memory_service": AsyncMock(),
            "claude_service": AsyncMock(),
            "vector_service": AsyncMock(),
            "graph_service": AsyncMock(),
            "embedding_service": AsyncMock()
        }
    
    def test_get_agents_status(self, client):
        """Test de l'endpoint de statut des agents"""
        response = client.get("/api/agents/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure de la réponse
        assert "available_agents" in data
        assert "available_workflows" in data
        assert "total_agents" in data
        assert "total_workflows" in data
        
        # Vérifier que tous les agents sont présents
        agent_names = [agent["name"] for agent in data["available_agents"]]
        expected_agents = ["consolidator", "validator", "pattern_extractor", "connector"]
        
        for expected_agent in expected_agents:
            assert expected_agent in agent_names
        
        # Vérifier que tous les workflows sont présents
        workflow_names = [workflow["name"] for workflow in data["available_workflows"]]
        expected_workflows = ["memory_consolidation", "knowledge_validation", "pattern_analysis", "multi_agent"]
        
        for expected_workflow in expected_workflows:
            assert expected_workflow in workflow_names
    
    def test_get_agents_health(self, client):
        """Test de l'endpoint de santé des agents"""
        response = client.get("/api/agents/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure de la réponse
        assert "status" in data
        assert "agents_initialized" in data
        assert "langgraph_ready" in data
        assert "workflows_available" in data
        assert "services" in data
        assert "timestamp" in data
        
        # Vérifier que le statut est healthy
        assert data["status"] == "healthy"
        assert data["agents_initialized"] is True
        assert data["langgraph_ready"] is True
    
    def test_get_agent_info_consolidator(self, client):
        """Test de l'endpoint d'information pour l'agent consolidator"""
        response = client.get("/api/agents/agents/consolidator/info")
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure de la réponse
        assert "name" in data
        assert "description" in data
        assert "capabilities" in data
        assert "input_format" in data
        assert "output_format" in data
        
        # Vérifier le contenu spécifique
        assert data["name"] == "ConsolidatorAgent"
        assert "consolidation" in data["description"].lower()
        assert len(data["capabilities"]) > 0
    
    def test_get_agent_info_validator(self, client):
        """Test de l'endpoint d'information pour l'agent validator"""
        response = client.get("/api/agents/agents/validator/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "ValidatorAgent"
        assert "validation" in data["description"].lower()
        assert "contradiction" in data["description"].lower()
    
    def test_get_agent_info_pattern_extractor(self, client):
        """Test de l'endpoint d'information pour l'agent pattern_extractor"""
        response = client.get("/api/agents/agents/pattern_extractor/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "PatternExtractorAgent"
        assert "pattern" in data["description"].lower()
    
    def test_get_agent_info_connector(self, client):
        """Test de l'endpoint d'information pour l'agent connector"""
        response = client.get("/api/agents/agents/connector/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["name"] == "ConnectorAgent"
        assert "graphe" in data["description"].lower()
    
    def test_get_agent_info_invalid_agent(self, client):
        """Test de l'endpoint d'information avec un agent invalide"""
        response = client.get("/api/agents/agents/invalid_agent/info")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_agent_consolidator(self, mock_get_services, client, mock_services):
        """Test d'exécution de l'agent consolidator"""
        mock_get_services.return_value = mock_services
        
        # Mock du résultat de l'agent
        mock_services["claude_service"].consolidate_memories = AsyncMock(return_value={
            "consolidated_memory": {"content": "test consolidated", "level": "L3"}
        })
        
        request_data = {
            "agent_type": "consolidator",
            "input_data": {
                "memory_data": [
                    {"id": 1, "content": "test memory 1"},
                    {"id": 2, "content": "test memory 2"}
                ]
            },
            "context": {"batch_size": 10},
            "config": {"timeout": 30}
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure de la réponse
        assert "agent_type" in data
        assert "result" in data
        assert "execution_time" in data
        assert "status" in data
        assert "timestamp" in data
        
        assert data["agent_type"] == "consolidator"
        assert isinstance(data["execution_time"], float)
        assert data["status"] in ["completed", "failed"]
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_agent_validator(self, mock_get_services, client, mock_services):
        """Test d'exécution de l'agent validator"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "agent_type": "validator",
            "input_data": {
                "knowledge_data": [
                    {"id": 1, "content": "Le ciel est bleu"},
                    {"id": 2, "content": "Le ciel est rouge"}
                ]
            },
            "context": {"validation_scope": "contradiction_detection"}
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "validator"
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_agent_pattern_extractor(self, mock_get_services, client, mock_services):
        """Test d'exécution de l'agent pattern_extractor"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "agent_type": "pattern_extractor",
            "input_data": {
                "data_sources": [
                    {"text": "Email: user@example.com"},
                    {"text": "Phone: 123-456-7890"}
                ]
            },
            "context": {"pattern_types": ["email", "phone"]}
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "pattern_extractor"
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_agent_connector(self, mock_get_services, client, mock_services):
        """Test d'exécution de l'agent connector"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "agent_type": "connector",
            "input_data": {
                "graph_data": {
                    "nodes": [{"id": 1, "name": "AI"}, {"id": 2, "name": "ML"}],
                    "edges": [{"source": 1, "target": 2}]
                }
            },
            "context": {"optimization_level": "basic"}
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["agent_type"] == "connector"
    
    def test_execute_agent_invalid_type(self, client):
        """Test d'exécution avec un type d'agent invalide"""
        request_data = {
            "agent_type": "invalid_agent",
            "input_data": {"test": "data"}
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        
        assert response.status_code == 200  # L'erreur est gérée dans la réponse
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] is not None
    
    def test_execute_agent_missing_data(self, client):
        """Test d'exécution avec des données manquantes"""
        request_data = {
            "agent_type": "consolidator"
            # input_data manquant
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        
        assert response.status_code == 422  # Erreur de validation Pydantic
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_workflow_memory_consolidation(self, mock_get_services, client, mock_services):
        """Test d'exécution du workflow de consolidation mémoire"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "workflow_type": "memory_consolidation",
            "parameters": {
                "batch_size": 50,
                "threshold": 0.8
            },
            "config": {"timeout": 60}
        }
        
        response = client.post("/api/agents/workflow", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Vérifier la structure de la réponse
        assert "workflow_type" in data
        assert "result" in data
        assert "execution_time" in data
        assert "status" in data
        assert "timestamp" in data
        assert "agents_used" in data
        
        assert data["workflow_type"] == "memory_consolidation"
        assert "consolidator" in data["agents_used"]
        assert "validator" in data["agents_used"]
        assert "connector" in data["agents_used"]
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_workflow_knowledge_validation(self, mock_get_services, client, mock_services):
        """Test d'exécution du workflow de validation des connaissances"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "workflow_type": "knowledge_validation",
            "parameters": {
                "scope": "priority",
                "validation_level": "comprehensive"
            }
        }
        
        response = client.post("/api/agents/workflow", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["workflow_type"] == "knowledge_validation"
        assert "validator" in data["agents_used"]
        assert "connector" in data["agents_used"]
        assert "pattern_extractor" in data["agents_used"]
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_workflow_pattern_analysis(self, mock_get_services, client, mock_services):
        """Test d'exécution du workflow d'analyse de patterns"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "workflow_type": "pattern_analysis",
            "parameters": {
                "data_sources": ["memory", "graph"],
                "time_range": {"start": "2024-01-01", "end": "2024-01-31"},
                "pattern_types": ["temporal", "semantic"],
                "depth_level": "comprehensive"
            }
        }
        
        response = client.post("/api/agents/workflow", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["workflow_type"] == "pattern_analysis"
        assert "pattern_extractor" in data["agents_used"]
    
    @patch('backend.api.routes.agents.get_services')
    def test_execute_workflow_multi_agent(self, mock_get_services, client, mock_services):
        """Test d'exécution du workflow multi-agents"""
        mock_get_services.return_value = mock_services
        
        request_data = {
            "workflow_type": "multi_agent",
            "parameters": {
                "execution_mode": "sequential",
                "workflow_type": "full_processing",
                "batch_size": 100
            }
        }
        
        response = client.post("/api/agents/workflow", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["workflow_type"] == "multi_agent"
        # Tous les agents doivent être utilisés
        expected_agents = ["consolidator", "validator", "pattern_extractor", "connector"]
        for agent in expected_agents:
            assert agent in data["agents_used"]
    
    def test_execute_workflow_invalid_type(self, client):
        """Test d'exécution avec un type de workflow invalide"""
        request_data = {
            "workflow_type": "invalid_workflow",
            "parameters": {"test": "data"}
        }
        
        response = client.post("/api/agents/workflow", json=request_data)
        
        assert response.status_code == 200  # L'erreur est gérée dans la réponse
        data = response.json()
        assert data["status"] == "failed"
        assert data["error"] is not None
    
    def test_execute_workflow_missing_parameters(self, client):
        """Test d'exécution de workflow avec des paramètres manquants"""
        request_data = {
            "workflow_type": "memory_consolidation"
            # parameters manquant
        }
        
        response = client.post("/api/agents/workflow", json=request_data)
        
        assert response.status_code == 422  # Erreur de validation Pydantic


class TestAgentsAPIValidation:
    """Tests de validation des données pour l'API des agents"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_agent_request_validation(self, client):
        """Test de validation des requêtes d'agents"""
        # Test avec des données valides
        valid_request = {
            "agent_type": "consolidator",
            "input_data": {"test": "data"},
            "context": {"additional": "info"},
            "config": {"timeout": 30}
        }
        
        response = client.post("/api/agents/execute", json=valid_request)
        assert response.status_code == 200
        
        # Test avec agent_type manquant
        invalid_request = {
            "input_data": {"test": "data"}
        }
        
        response = client.post("/api/agents/execute", json=invalid_request)
        assert response.status_code == 422
        
        # Test avec input_data manquant
        invalid_request = {
            "agent_type": "consolidator"
        }
        
        response = client.post("/api/agents/execute", json=invalid_request)
        assert response.status_code == 422
    
    def test_workflow_request_validation(self, client):
        """Test de validation des requêtes de workflows"""
        # Test avec des données valides
        valid_request = {
            "workflow_type": "memory_consolidation",
            "parameters": {"batch_size": 50},
            "config": {"timeout": 60}
        }
        
        response = client.post("/api/agents/workflow", json=valid_request)
        assert response.status_code == 200
        
        # Test avec workflow_type manquant
        invalid_request = {
            "parameters": {"batch_size": 50}
        }
        
        response = client.post("/api/agents/workflow", json=invalid_request)
        assert response.status_code == 422
        
        # Test avec parameters manquant
        invalid_request = {
            "workflow_type": "memory_consolidation"
        }
        
        response = client.post("/api/agents/workflow", json=invalid_request)
        assert response.status_code == 422
    
    def test_response_format_validation(self, client):
        """Test de validation du format des réponses"""
        # Test de la réponse d'exécution d'agent
        request_data = {
            "agent_type": "consolidator",
            "input_data": {"test": "data"}
        }
        
        response = client.post("/api/agents/execute", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        
        # Vérifier que tous les champs requis sont présents
        required_fields = ["agent_type", "result", "execution_time", "status", "timestamp"]
        for field in required_fields:
            assert field in data
        
        # Vérifier les types de données
        assert isinstance(data["agent_type"], str)
        assert isinstance(data["result"], dict)
        assert isinstance(data["execution_time"], (int, float))
        assert isinstance(data["status"], str)
        assert isinstance(data["timestamp"], str)
        
        # Vérifier que le statut est valide
        assert data["status"] in ["completed", "failed", "running"]


class TestAgentsAPIPerformance:
    """Tests de performance pour l'API des agents"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_api_response_time(self, client):
        """Test du temps de réponse de l'API"""
        import time
        
        # Test de l'endpoint de statut (doit être rapide)
        start_time = time.time()
        response = client.get("/api/agents/status")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Moins d'1 seconde
        
        # Test de l'endpoint de santé
        start_time = time.time()
        response = client.get("/api/agents/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Moins d'1 seconde
    
    def test_concurrent_requests(self, client):
        """Test de requêtes concurrentes"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get("/api/agents/status")
            results.append(response.status_code)
        
        # Créer plusieurs threads pour des requêtes concurrentes
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Démarrer tous les threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Attendre que tous les threads se terminent
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Vérifier que toutes les requêtes ont réussi
        assert len(results) == 10
        assert all(status == 200 for status in results)
        
        # Vérifier que le temps total est raisonnable
        assert total_time < 5.0  # Moins de 5 secondes pour 10 requêtes


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])