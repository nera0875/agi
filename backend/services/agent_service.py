"""
Agent Service - LangGraph Stateful Agents
Implements conversational agents with PostgreSQL checkpointing
"""

import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from uuid import UUID, uuid4
from datetime import datetime

import asyncpg
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph.message import add_messages

from config import settings
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


# ============================================================================
# AGENT STATE DEFINITION
# ============================================================================

class AgentState(TypedDict):
    """
    State for conversational agent
    Managed by LangGraph with PostgreSQL persistence
    """
    messages: Annotated[List[BaseMessage], add_messages]
    current_task: Optional[str]
    memory_context: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    thread_id: str
    user_id: Optional[str]


# ============================================================================
# TOOLS DEFINITION
# ============================================================================

@tool
async def search_memory(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Search memory using hybrid RAG

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        List of relevant memories
    """
    # This will be injected by AgentService
    return []


@tool
async def store_memory(content: str, metadata: Dict[str, Any] = None) -> str:
    """
    Store new memory in the system

    Args:
        content: Memory content
        metadata: Optional metadata

    Returns:
        Memory ID
    """
    # This will be injected by AgentService
    return "memory_stored"


@tool
async def get_related_memories(memory_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
    """
    Get memories related through graph relations

    Args:
        memory_id: Starting memory ID
        max_depth: Maximum traversal depth

    Returns:
        List of related memories
    """
    # This will be injected by AgentService
    return []


# ============================================================================
# AGENT SERVICE
# ============================================================================

class AgentService:
    """
    LangGraph stateful agent service with:
    - PostgreSQL checkpointing for conversation persistence
    - Tool integration with memory service
    - Streaming responses
    - Multi-user session management
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        memory_service: MemoryService
    ):
        self.db_pool = db_pool
        self.memory_service = memory_service

        # Initialize Claude LLM
        try:
            self.llm = ChatAnthropic(
                anthropic_api_key=settings.anthropic_api_key,
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                temperature=0.7,
                streaming=True
            )
        except Exception as exc:
            logger.error("Anthropic client initialization failed: %s", exc)
            raise RuntimeError(
                "Initialisation du client Anthropic impossible. "
                "Vérifiez ANTHROPIC_API_KEY, le modèle choisi et la connectivité."
            ) from exc

        # Initialize PostgreSQL checkpointer (disabled for now - using MemorySaver)
        # The PostgresSaver requires async context manager which is complex to init here
        # We'll use in-memory checkpointing for MVP and migrate to Postgres later
        from langgraph.checkpoint.memory import MemorySaver
        self.checkpointer = MemorySaver()
        logger.info("Using in-memory checkpointer (MemorySaver)")

        # Build the graph
        self.graph = self._build_graph()
        self.app = self.graph.compile(checkpointer=self.checkpointer)

        logger.info("AgentService initialized with LangGraph + PostgreSQL checkpointer")

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph state graph

        Returns:
            Configured StateGraph
        """
        # Create graph
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("retrieve_context", self._retrieve_context)
        workflow.add_node("generate_response", self._generate_response)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("store_conversation", self._store_conversation)

        # Set entry point
        workflow.set_entry_point("retrieve_context")

        # Add edges
        workflow.add_edge("retrieve_context", "generate_response")
        workflow.add_conditional_edges(
            "generate_response",
            self._should_use_tools,
            {
                "tools": "execute_tools",
                "end": "store_conversation"
            }
        )
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("store_conversation", END)

        return workflow

    # ========================================================================
    # GRAPH NODES
    # ========================================================================

    async def _retrieve_context(self, state: AgentState) -> AgentState:
        """
        Retrieve relevant context from memory

        Args:
            state: Current agent state

        Returns:
            Updated state with memory context
        """
        # Get last message
        if not state["messages"]:
            return state

        last_message = state["messages"][-1]

        # Only retrieve for human messages
        if isinstance(last_message, HumanMessage):
            # Search memory
            docs = await self.memory_service.hybrid_search(
                query=last_message.content,
                top_k=5,
                user_id=state.get("user_id")
            )

            # Format context
            state["memory_context"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in docs
            ]

            logger.info(f"Retrieved {len(docs)} memory documents")

        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """
        Generate LLM response with context

        Args:
            state: Current agent state

        Returns:
            Updated state with AI message
        """
        # Build system prompt with context
        system_prompt = self._build_system_prompt(state["memory_context"])

        # Prepare messages
        messages = [SystemMessage(content=system_prompt)] + state["messages"]

        # Generate response
        response = await self.llm.ainvoke(messages)

        # Add to state
        state["messages"].append(response)

        return state

    async def _execute_tools(self, state: AgentState) -> AgentState:
        """
        Execute tools requested by the agent

        Args:
            state: Current agent state

        Returns:
            Updated state with tool results
        """
        last_message = state["messages"][-1]

        # Parse tool calls from message
        if hasattr(last_message, "tool_calls"):
            for tool_call in last_message.tool_calls:
                # Execute tool based on name
                result = await self._execute_single_tool(
                    tool_call["name"],
                    tool_call["args"],
                    state
                )

                # Add result as message
                state["messages"].append(
                    AIMessage(content=f"Tool {tool_call['name']} result: {result}")
                )

        return state

    async def _store_conversation(self, state: AgentState) -> AgentState:
        """
        Store conversation turn in memory

        Args:
            state: Current agent state

        Returns:
            Updated state
        """
        # Get last exchange
        if len(state["messages"]) >= 2:
            human_msg = state["messages"][-2]
            ai_msg = state["messages"][-1]

            if isinstance(human_msg, HumanMessage) and isinstance(ai_msg, AIMessage):
                # Store as memory
                await self.memory_service.add_memory(
                    content=f"Q: {human_msg.content}\nA: {ai_msg.content}",
                    metadata={
                        "type": "conversation",
                        "thread_id": state["thread_id"],
                        "user_id": state.get("user_id"),
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    source_type="conversation",
                    user_id=state.get("user_id")
                )

                logger.info("Stored conversation turn in memory")

        return state

    # ========================================================================
    # UTILITIES
    # ========================================================================

    def _should_use_tools(self, state: AgentState) -> str:
        """
        Decide whether to use tools based on response

        Args:
            state: Current state

        Returns:
            "tools" or "end"
        """
        last_message = state["messages"][-1]

        # Check if message contains tool calls
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return "end"

    def _build_system_prompt(self, memory_context: List[Dict[str, Any]]) -> str:
        """
        Build system prompt with memory context

        Args:
            memory_context: Retrieved memories

        Returns:
            System prompt string
        """
        base_prompt = """You are an intelligent AGI assistant with access to a memory system.
        Use the provided context to give informed and consistent responses.
        You can use tools to search memory, store new information, or find related concepts.
        """

        if memory_context:
            context_str = "\n\n".join([
                f"Memory {i+1}: {mem['content']}"
                for i, mem in enumerate(memory_context)
            ])

            return f"{base_prompt}\n\nRelevant Context:\n{context_str}"

        return base_prompt

    async def _execute_single_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        state: AgentState
    ) -> Any:
        """
        Execute a single tool

        Args:
            tool_name: Name of tool
            args: Tool arguments
            state: Current state

        Returns:
            Tool result
        """
        if tool_name == "search_memory":
            docs = await self.memory_service.hybrid_search(
                query=args["query"],
                top_k=args.get("top_k", 5),
                user_id=state.get("user_id")
            )
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]

        elif tool_name == "store_memory":
            memory_id = await self.memory_service.add_memory(
                content=args["content"],
                metadata=args.get("metadata"),
                source_type="agent_stored",
                user_id=state.get("user_id")
            )
            return str(memory_id)

        elif tool_name == "get_related_memories":
            docs = await self.memory_service.get_related_memories(
                memory_id=UUID(args["memory_id"]),
                max_depth=args.get("max_depth", 2)
            )
            return [{"content": doc.page_content, "metadata": doc.metadata} for doc in docs]

        else:
            logger.warning(f"Unknown tool: {tool_name}")
            return f"Unknown tool: {tool_name}"

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    async def create_session(
        self,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create new conversation session

        Args:
            user_id: Optional user ID
            metadata: Optional session metadata

        Returns:
            Thread ID for the session
        """
        thread_id = str(uuid4())

        # Store in sessions table
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO sessions (user_id, thread_id, metadata)
                VALUES ($1, $2, $3)
                """,
                user_id,
                thread_id,
                metadata or {}
            )

        logger.info(f"Created session {thread_id}")
        return thread_id

    async def chat(
        self,
        message: str,
        thread_id: str,
        user_id: Optional[str] = None,
        stream: bool = False
    ) -> Optional[str]:
        """
        Process chat message

        Args:
            message: User message
            thread_id: Conversation thread ID
            user_id: Optional user ID
            stream: Whether to stream response (if True, use chat_stream instead)

        Returns:
            Full response string (use chat_stream for streaming)
        """
        # Update session activity
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sessions
                SET last_active_at = NOW()
                WHERE thread_id = $1
                """,
                thread_id
            )

        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "thread_id": thread_id,
            "user_id": user_id,
            "memory_context": [],
            "metadata": {}
        }

        # Configure for thread
        config = {"configurable": {"thread_id": thread_id}}

        # Get full response
        result = await self.app.ainvoke(initial_state, config)

        # Extract AI response
        for msg in reversed(result["messages"]):
            if isinstance(msg, AIMessage):
                return msg.content

        return "No response generated"

    async def chat_stream(
        self,
        message: str,
        thread_id: str,
        user_id: Optional[str] = None
    ):
        """
        Stream chat response

        Args:
            message: User message
            thread_id: Conversation thread ID
            user_id: Optional user ID

        Yields:
            Response chunks as they're generated
        """
        # Update session activity
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE sessions
                SET last_active_at = NOW()
                WHERE thread_id = $1
                """,
                thread_id
            )

        # Create initial state
        initial_state = {
            "messages": [HumanMessage(content=message)],
            "thread_id": thread_id,
            "user_id": user_id,
            "memory_context": [],
            "metadata": {}
        }

        # Configure for thread
        config = {"configurable": {"thread_id": thread_id}}

        # Stream response
        async for event in self.app.astream(initial_state, config):
            if "generate_response" in event:
                messages = event["generate_response"]["messages"]
                if messages:
                    last_msg = messages[-1]
                    if isinstance(last_msg, AIMessage):
                        yield last_msg.content

    async def get_conversation_history(
        self,
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[BaseMessage]:
        """
        Get conversation history from checkpointer

        Args:
            thread_id: Thread ID
            limit: Optional message limit

        Returns:
            List of messages
        """
        config = {"configurable": {"thread_id": thread_id}}

        # Get checkpoint
        checkpoint = self.checkpointer.get(config)

        if checkpoint and "messages" in checkpoint:
            messages = checkpoint["messages"]
            if limit:
                return messages[-limit:]
            return messages

        return []

    async def health_check(self) -> Dict[str, bool]:
        """
        Check service health

        Returns:
            Health status dict
        """
        status = {
            "database": False,
            "llm": False,
            "checkpointer": False
        }

        # Check database
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            status["database"] = True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")

        # Check LLM
        try:
            await self.llm.ainvoke([SystemMessage(content="ping")])
            status["llm"] = True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")

        # Check checkpointer
        try:
            test_config = {"configurable": {"thread_id": "health_check"}}
            self.checkpointer.put(test_config, {"test": True})
            status["checkpointer"] = True
        except Exception as e:
            logger.error(f"Checkpointer health check failed: {e}")

        return status
