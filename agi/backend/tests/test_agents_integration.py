"""
Tests d'intégration pour les agents LangGraph
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, Any

from ..agents.consolidator_agent import ConsolidatorAgent
from ..agents.validator_agent import ValidatorAgent
from ..agents.pattern_extractor_agent import PatternExtractorAgent
from ..agents.connector_agent import ConnectorAgent
from ..agents.workflows.multi_agent_orchestrator import MultiAgentOrchestrator
from ..agents.workflows.memory_consolidation_workflow import MemoryConsolidationWorkflow
from ..agents.workflows.knowledge_validation_workflow import KnowledgeValidationWorkflow
from ..agents.workflows.pattern_analysis_workflow import PatternAnalysisWorkflow, AnalysisScope
from ..agents.base_agent import AgentConfig, AgentState


class TestAgentsIntegration:
    """Tests d'intégration pour les agents LangGraph"""
    
    @pytest.fixture
    def mock_services(self):
        """Services mockés pour les tests"""
        return {
            "memory_service": Mock(),
            "claude_service": AsyncMock(),
            "vector_service": Mock(),
            "graph_service": Mock(),
            "embedding_service": Mock()
        }
    
    @pytest.fixture
    def agent_config(self):
        """Configuration d'agent pour les tests"""
        return AgentConfig(
            name="test_agent",
            description="Agent de test",
            max_iterations=5,
            timeout=30.0
        )
    
    @pytest.fixture
    def sample_agent_state(self):
        """État d'agent exemple pour les tests"""
        return AgentState(
            messages=[],
            context={
                "input_data": {"test": "data"},
                "execution_start": datetime.now().isoformat()
            },
            step_count=0
        )


class TestConsolidatorAgent(TestAgentsIntegration):
    """Tests pour ConsolidatorAgent"""
    
    @pytest.mark.asyncio
    async def test_consolidator_agent_initialization(self, agent_config, mock_services):
        """Test d'initialisation du ConsolidatorAgent"""
        agent = ConsolidatorAgent(agent_config, mock_services)
        
        assert agent.config.name == "test_agent"
        assert agent.services == mock_services
        assert hasattr(agent, 'workflow')
    
    @pytest.mark.asyncio
    async def test_consolidator_agent_process(self, agent_config, mock_services, sample_agent_state):
        """Test du processus de consolidation"""
        # Mock des services
        mock_services["memory_service"].get_l2_memories = AsyncMock(return_value=[
            {"id": 1, "content": "test memory 1", "timestamp": "2024-01-01"},
            {"id": 2, "content": "test memory 2", "timestamp": "2024-01-02"}
        ])
        
        mock_services["claude_service"].consolidate_memories = AsyncMock(return_value={
            "consolidated_memory": {"content": "consolidated test", "level": "L3"},
            "consolidation_score": 0.85
        })
        
        mock_services["memory_service"].store_l3_memory = AsyncMock(return_value={"id": 3})
        mock_services["memory_service"].cleanup_l2_memories = AsyncMock(return_value={"cleaned": 2})
        
        # Créer et exécuter l'agent
        agent = ConsolidatorAgent(agent_config, mock_services)
        
        # Ajouter des données de test à l'état
        sample_agent_state.context["memory_data"] = [
            {"id": 1, "content": "test memory 1"},
            {"id": 2, "content": "test memory 2"}
        ]
        
        result = await agent.process(sample_agent_state)
        
        # Vérifications
        assert result is not None
        assert "consolidated_memories" in result.get("context", {})
        
        # Vérifier que les services ont été appelés
        mock_services["claude_service"].consolidate_memories.assert_called()
        mock_services["memory_service"].store_l3_memory.assert_called()
    
    @pytest.mark.asyncio
    async def test_consolidator_agent_error_handling(self, agent_config, mock_services, sample_agent_state):
        """Test de gestion d'erreur du ConsolidatorAgent"""
        # Mock d'une erreur dans Claude
        mock_services["claude_service"].consolidate_memories = AsyncMock(
            side_effect=Exception("Claude service error")
        )
        
        agent = ConsolidatorAgent(agent_config, mock_services)
        sample_agent_state.context["memory_data"] = [{"id": 1, "content": "test"}]
        
        result = await agent.process(sample_agent_state)
        
        # Vérifier que l'erreur est gérée
        assert "error" in result


class TestValidatorAgent(TestAgentsIntegration):
    """Tests pour ValidatorAgent"""
    
    @pytest.mark.asyncio
    async def test_validator_agent_contradiction_detection(self, agent_config, mock_services, sample_agent_state):
        """Test de détection de contradictions"""
        # Mock des données avec contradictions
        mock_services["memory_service"].get_knowledge_data = AsyncMock(return_value=[
            {"id": 1, "content": "Le ciel est bleu", "confidence": 0.9},
            {"id": 2, "content": "Le ciel est rouge", "confidence": 0.8}
        ])
        
        mock_services["claude_service"].detect_contradictions = AsyncMock(return_value={
            "contradictions": [
                {
                    "items": [1, 2],
                    "type": "direct_contradiction",
                    "confidence": 0.95
                }
            ]
        })
        
        agent = ValidatorAgent(agent_config, mock_services)
        sample_agent_state.context["knowledge_data"] = [
            {"id": 1, "content": "Le ciel est bleu"},
            {"id": 2, "content": "Le ciel est rouge"}
        ]
        
        result = await agent.process(sample_agent_state)
        
        # Vérifications
        assert result is not None
        assert "contradictions_found" in result.get("context", {})
        mock_services["claude_service"].detect_contradictions.assert_called()
    
    @pytest.mark.asyncio
    async def test_validator_agent_consistency_validation(self, agent_config, mock_services, sample_agent_state):
        """Test de validation de cohérence"""
        mock_services["vector_service"].semantic_similarity = AsyncMock(return_value=0.85)
        mock_services["claude_service"].validate_consistency = AsyncMock(return_value={
            "consistency_score": 0.92,
            "issues": []
        })
        
        agent = ValidatorAgent(agent_config, mock_services)
        sample_agent_state.context["validation_scope"] = "semantic"
        
        result = await agent.process(sample_agent_state)
        
        assert result is not None
        assert "validation_results" in result.get("context", {})


class TestPatternExtractorAgent(TestAgentsIntegration):
    """Tests pour PatternExtractorAgent"""
    
    @pytest.mark.asyncio
    async def test_pattern_extractor_basic_patterns(self, agent_config, mock_services, sample_agent_state):
        """Test d'extraction de patterns basiques"""
        # Mock des données d'entrée
        sample_data = [
            {"text": "Email: user@example.com", "timestamp": "2024-01-01"},
            {"text": "Contact: admin@test.org", "timestamp": "2024-01-02"},
            {"text": "Phone: 123-456-7890", "timestamp": "2024-01-03"}
        ]
        
        agent = PatternExtractorAgent(agent_config, mock_services)
        sample_agent_state.context["data_sources"] = sample_data
        sample_agent_state.context["pattern_types"] = ["email", "phone"]
        
        result = await agent.process(sample_agent_state)
        
        # Vérifications
        assert result is not None
        context = result.get("context", {})
        assert "extracted_patterns" in context
        
        # Vérifier que des patterns d'email ont été trouvés
        patterns = context.get("extracted_patterns", {})
        assert "email" in patterns
    
    @pytest.mark.asyncio
    async def test_pattern_extractor_semantic_analysis(self, agent_config, mock_services, sample_agent_state):
        """Test d'analyse sémantique"""
        mock_services["embedding_service"].get_embeddings = AsyncMock(return_value=[
            [0.1, 0.2, 0.3],  # embedding pour "technology"
            [0.15, 0.25, 0.35]  # embedding pour "innovation"
        ])
        
        mock_services["claude_service"].extract_concepts = AsyncMock(return_value={
            "concepts": [
                {"name": "technology", "confidence": 0.9, "category": "domain"},
                {"name": "innovation", "confidence": 0.85, "category": "concept"}
            ]
        })
        
        agent = PatternExtractorAgent(agent_config, mock_services)
        sample_agent_state.context["data_sources"] = [
            {"text": "Technology drives innovation in modern society"}
        ]
        sample_agent_state.context["analysis_depth"] = "semantic"
        
        result = await agent.process(sample_agent_state)
        
        assert result is not None
        assert "concepts" in result.get("context", {})
        mock_services["claude_service"].extract_concepts.assert_called()


class TestConnectorAgent(TestAgentsIntegration):
    """Tests pour ConnectorAgent"""
    
    @pytest.mark.asyncio
    async def test_connector_agent_graph_analysis(self, agent_config, mock_services, sample_agent_state):
        """Test d'analyse du graphe"""
        # Mock du graphe existant
        mock_graph_data = {
            "nodes": [
                {"id": 1, "type": "concept", "name": "AI"},
                {"id": 2, "type": "concept", "name": "Machine Learning"},
                {"id": 3, "type": "concept", "name": "Deep Learning"}
            ],
            "edges": [
                {"source": 1, "target": 2, "type": "includes"}
            ]
        }
        
        mock_services["graph_service"].get_graph_structure = AsyncMock(return_value=mock_graph_data)
        mock_services["graph_service"].analyze_connectivity = AsyncMock(return_value={
            "density": 0.33,
            "missing_connections": [
                {"source": 2, "target": 3, "type": "includes", "confidence": 0.9}
            ]
        })
        
        agent = ConnectorAgent(agent_config, mock_services)
        sample_agent_state.context["graph_data"] = mock_graph_data
        
        result = await agent.process(sample_agent_state)
        
        # Vérifications
        assert result is not None
        context = result.get("context", {})
        assert "graph_analysis" in context
        assert "missing_connections" in context
        
        mock_services["graph_service"].analyze_connectivity.assert_called()
    
    @pytest.mark.asyncio
    async def test_connector_agent_connection_optimization(self, agent_config, mock_services, sample_agent_state):
        """Test d'optimisation des connexions"""
        mock_services["graph_service"].optimize_connections = AsyncMock(return_value={
            "optimized_connections": 5,
            "removed_redundant": 2,
            "quality_improvement": 0.15
        })
        
        agent = ConnectorAgent(agent_config, mock_services)
        sample_agent_state.context["optimization_level"] = "comprehensive"
        
        result = await agent.process(sample_agent_state)
        
        assert result is not None
        assert "optimization_report" in result.get("context", {})
        mock_services["graph_service"].optimize_connections.assert_called()


class TestWorkflowsIntegration:
    """Tests d'intégration pour les workflows"""
    
    @pytest.fixture
    def mock_services(self):
        """Services mockés pour les workflows"""
        return {
            "memory_service": AsyncMock(),
            "claude_service": AsyncMock(),
            "vector_service": AsyncMock(),
            "graph_service": AsyncMock(),
            "embedding_service": AsyncMock()
        }
    
    @pytest.mark.asyncio
    async def test_memory_consolidation_workflow(self, mock_services):
        """Test du workflow de consolidation mémoire"""
        # Mock des données L2
        mock_services["memory_service"].get_consolidation_candidates = AsyncMock(return_value=[
            {"id": 1, "content": "memory 1", "score": 0.9},
            {"id": 2, "content": "memory 2", "score": 0.85}
        ])
        
        workflow = MemoryConsolidationWorkflow(mock_services)
        
        result = await workflow.run_consolidation(
            batch_size=10,
            threshold=0.8,
            config={}
        )
        
        # Vérifications
        assert result is not None
        assert "consolidation_report" in result
        mock_services["memory_service"].get_consolidation_candidates.assert_called()
    
    @pytest.mark.asyncio
    async def test_knowledge_validation_workflow(self, mock_services):
        """Test du workflow de validation des connaissances"""
        mock_services["memory_service"].get_validation_scope = AsyncMock(return_value={
            "total_items": 100,
            "priority_items": 20
        })
        
        workflow = KnowledgeValidationWorkflow(mock_services)
        
        result = await workflow.run_validation(
            scope="priority",
            validation_level="comprehensive",
            config={}
        )
        
        assert result is not None
        assert "validation_report" in result
    
    @pytest.mark.asyncio
    async def test_pattern_analysis_workflow(self, mock_services):
        """Test du workflow d'analyse de patterns"""
        analysis_scope = AnalysisScope(
            data_sources=["memory", "graph"],
            time_range={"start": "2024-01-01", "end": "2024-01-31"},
            pattern_types=["temporal", "semantic"],
            depth_level="comprehensive"
        )
        
        workflow = PatternAnalysisWorkflow(mock_services)
        
        result = await workflow.run_analysis(
            scope=analysis_scope,
            config={}
        )
        
        assert result is not None
        assert "analysis_report" in result
    
    @pytest.mark.asyncio
    async def test_multi_agent_orchestrator(self, mock_services):
        """Test de l'orchestrateur multi-agents"""
        orchestrator = MultiAgentOrchestrator(mock_services)
        
        result = await orchestrator.execute_workflow(
            workflow_type="full_processing",
            execution_mode="sequential",
            parameters={"batch_size": 50},
            config={}
        )
        
        assert result is not None
        assert "execution_report" in result


class TestAgentsErrorHandling:
    """Tests de gestion d'erreurs pour les agents"""
    
    @pytest.fixture
    def failing_services(self):
        """Services qui échouent pour tester la gestion d'erreurs"""
        return {
            "memory_service": Mock(side_effect=Exception("Memory service error")),
            "claude_service": AsyncMock(side_effect=Exception("Claude service error")),
            "vector_service": Mock(side_effect=Exception("Vector service error")),
            "graph_service": Mock(side_effect=Exception("Graph service error"))
        }
    
    @pytest.mark.asyncio
    async def test_agent_resilience_to_service_failures(self, failing_services):
        """Test de résilience des agents aux pannes de services"""
        config = AgentConfig(name="test_agent", description="Test")
        state = AgentState(messages=[], context={"test": "data"}, step_count=0)
        
        # Tester chaque agent avec des services défaillants
        agents = [
            ConsolidatorAgent(config, failing_services),
            ValidatorAgent(config, failing_services),
            PatternExtractorAgent(config, failing_services),
            ConnectorAgent(config, failing_services)
        ]
        
        for agent in agents:
            result = await agent.process(state)
            # L'agent doit retourner un résultat même en cas d'erreur
            assert result is not None
            # L'erreur doit être capturée et reportée
            assert "error" in result or result.get("context", {}).get("status") == "failed"
    
    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, failing_services):
        """Test de récupération d'erreurs dans les workflows"""
        # Tester que les workflows gèrent gracieusement les erreurs
        workflows = [
            MemoryConsolidationWorkflow(failing_services),
            KnowledgeValidationWorkflow(failing_services),
            PatternAnalysisWorkflow(failing_services)
        ]
        
        for workflow in workflows:
            # Chaque workflow doit avoir une méthode de gestion d'erreur
            assert hasattr(workflow, 'handle_error') or hasattr(workflow, 'error_recovery')


class TestAgentsPerformance:
    """Tests de performance pour les agents"""
    
    @pytest.mark.asyncio
    async def test_agent_execution_time(self, mock_services):
        """Test du temps d'exécution des agents"""
        config = AgentConfig(name="perf_test", description="Performance test")
        state = AgentState(messages=[], context={"data": list(range(100))}, step_count=0)
        
        agents = [
            ConsolidatorAgent(config, mock_services),
            ValidatorAgent(config, mock_services),
            PatternExtractorAgent(config, mock_services),
            ConnectorAgent(config, mock_services)
        ]
        
        for agent in agents:
            start_time = datetime.now()
            result = await agent.process(state)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Vérifier que l'exécution ne prend pas trop de temps (seuil arbitraire)
            assert execution_time < 30.0  # 30 secondes max
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(self, mock_services):
        """Test d'exécution concurrente des agents"""
        config = AgentConfig(name="concurrent_test", description="Concurrent test")
        state = AgentState(messages=[], context={"data": "test"}, step_count=0)
        
        # Créer plusieurs instances d'agents
        agents = [
            ConsolidatorAgent(config, mock_services),
            ValidatorAgent(config, mock_services),
            PatternExtractorAgent(config, mock_services),
            ConnectorAgent(config, mock_services)
        ]
        
        # Exécuter tous les agents en parallèle
        tasks = [agent.process(state) for agent in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Vérifier que tous les agents ont terminé
        assert len(results) == 4
        for result in results:
            assert not isinstance(result, Exception)
            assert result is not None


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])