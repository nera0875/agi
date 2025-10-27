"""
Base Agent class for all LangGraph agents in AGI-V2.
Provides common functionality and interfaces for all agents.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class AgentState(TypedDict):
    """Base state structure for all agents."""
    messages: List[BaseMessage]
    context: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str]
    step_count: int


class AgentConfig(BaseModel):
    """Configuration for agents."""
    name: str
    description: str
    max_steps: int = Field(default=10, ge=1, le=100)
    timeout: int = Field(default=300, ge=30, le=3600)  # seconds
    retry_count: int = Field(default=3, ge=0, le=10)
    enable_logging: bool = True


class BaseAgent(ABC):
    """
    Abstract base class for all LangGraph agents.
    
    Provides common functionality:
    - State management
    - Error handling
    - Logging
    - Configuration
    - Graph construction
    """
    
    def __init__(self, config: AgentConfig, services: Dict[str, Any]):
        self.config = config
        self.services = services
        self.logger = logger.bind(agent=config.name)
        self._graph: Optional[StateGraph] = None
        
    @property
    def name(self) -> str:
        return self.config.name
    
    @property
    def graph(self) -> StateGraph:
        """Get the compiled LangGraph."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph
    
    @abstractmethod
    def _build_graph(self) -> StateGraph:
        """Build and return the LangGraph for this agent."""
        pass
    
    @abstractmethod
    async def process(self, state: AgentState) -> AgentState:
        """Main processing method for the agent."""
        pass
    
    def create_initial_state(self, 
                           messages: List[BaseMessage] = None,
                           context: Dict[str, Any] = None,
                           metadata: Dict[str, Any] = None) -> AgentState:
        """Create initial state for the agent."""
        return AgentState(
            messages=messages or [],
            context=context or {},
            metadata=metadata or {},
            error=None,
            step_count=0
        )
    
    async def run(self, initial_state: AgentState) -> AgentState:
        """Run the agent with the given initial state."""
        try:
            self.logger.info("Starting agent execution", 
                           initial_context=initial_state.get("context", {}))
            
            # Run the graph
            result = await self.graph.ainvoke(initial_state)
            
            self.logger.info("Agent execution completed successfully",
                           final_step_count=result.get("step_count", 0))
            
            return result
            
        except Exception as e:
            self.logger.error("Agent execution failed", error=str(e))
            return AgentState(
                messages=initial_state.get("messages", []),
                context=initial_state.get("context", {}),
                metadata=initial_state.get("metadata", {}),
                error=str(e),
                step_count=initial_state.get("step_count", 0)
            )
    
    def _increment_step(self, state: AgentState) -> AgentState:
        """Increment step counter in state."""
        state["step_count"] = state.get("step_count", 0) + 1
        return state
    
    def _should_continue(self, state: AgentState) -> bool:
        """Check if agent should continue processing."""
        if state.get("error"):
            return False
        if state.get("step_count", 0) >= self.config.max_steps:
            self.logger.warning("Max steps reached", max_steps=self.config.max_steps)
            return False
        return True
    
    def _log_step(self, step_name: str, state: AgentState, **kwargs):
        """Log a processing step."""
        if self.config.enable_logging:
            self.logger.info(f"Agent step: {step_name}",
                           step_count=state.get("step_count", 0),
                           **kwargs)


class AgentRegistry:
    """Registry for managing agent instances."""
    
    def __init__(self):
        self._agents: Dict[str, BaseAgent] = {}
    
    def register(self, agent: BaseAgent):
        """Register an agent."""
        self._agents[agent.name] = agent
    
    def get(self, name: str) -> Optional[BaseAgent]:
        """Get an agent by name."""
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agents.keys())
    
    def remove(self, name: str) -> bool:
        """Remove an agent from registry."""
        if name in self._agents:
            del self._agents[name]
            return True
        return False


# Global agent registry
agent_registry = AgentRegistry()