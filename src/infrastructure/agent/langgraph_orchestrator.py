"""LangGraph orchestrator implementation with ReAct pattern."""
from datetime import datetime
from typing import Annotated, Any, AsyncIterator, TypedDict

from langchain_aws import ChatBedrockConverse
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from src.application.interfaces.agent_orchestrator import IAgentOrchestrator
from src.domain.entities.query_result import AgentStep, QueryResult, StreamEvent
from src.domain.interfaces.observability_service import IObservabilityService
from src.infrastructure.agent.tools import AgentTools
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State for the agent graph.

    messages uses Annotated with add_messages reducer so returned messages
    are appended to the list (not replaced). This is critical for the
    Converse API which requires full message history with tool_use/tool_result pairs.
    """

    messages: Annotated[list, add_messages]
    reasoning_steps: list[dict[str, Any]]
    final_answer: str | None


class LangGraphOrchestrator(IAgentOrchestrator):
    """Agent orchestrator using LangGraph with ReAct pattern."""

    def __init__(
        self,
        llm_model_id: str,
        region: str,
        agent_tools: AgentTools,
        observability_service: IObservabilityService | None = None,
    ) -> None:
        """
        Initialize LangGraph orchestrator.

        Args:
            llm_model_id: AWS Bedrock model ID (supports cross-region inference profiles)
            region: AWS region
            agent_tools: Agent tools factory
            observability_service: Optional observability service (Langfuse or LangSmith)
        """
        logger.info(
            "Initializing LangGraph orchestrator",
            extra={"model_id": llm_model_id, "region": region},
        )

        # ChatBedrockConverse uses Converse API - supports cross-region inference profiles
        self._llm = ChatBedrockConverse(
            model=llm_model_id,
            region_name=region,
            temperature=0.7,
            max_tokens=2048,
        )

        self._tools = agent_tools.create_tools()
        self._llm_with_tools = self._llm.bind_tools(self._tools)
        self._observability = observability_service

        logger.info(f"Agent tools configured: {len(self._tools)} tools available")

        # Build the graph
        self._graph = self._build_graph()
        logger.info("LangGraph workflow compiled successfully")

    def _build_graph(self) -> Any:
        """Build the LangGraph workflow using Graph API."""
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self._tools))

        # Define edges using START constant
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            ["tools", END],
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    async def _agent_node(self, state: AgentState) -> dict:
        """Agent reasoning node - invokes LLM with tools."""
        messages = state["messages"]
        response = await self._llm_with_tools.ainvoke(messages)

        # Track reasoning steps for tool calls
        new_steps = []
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                new_steps.append(
                    {
                        "action": tool_call["name"],
                        "action_input": tool_call["args"],
                        "timestamp": datetime.now(),
                    }
                )

        return {
            "messages": [response],
            "reasoning_steps": state["reasoning_steps"] + new_steps,
        }

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue to tools or end."""
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return END

    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent."""
        return """You are a helpful financial AI agent specialized in stock market analysis and Amazon's financial information.

You have access to the following tools:
1. retrieve_realtime_stock_price: Get current stock price for any ticker symbol
2. retrieve_historical_stock_price: Get historical price data over a date range
3. search_financial_documents: Search Amazon's financial documents (annual reports, quarterly earnings)

When answering questions:
- Use tools to gather factual, up-to-date information
- Provide clear, concise answers based on the retrieved data
- When comparing data, use the appropriate tools to get both pieces of information
- If you need historical data, remember that Q4 spans October-December
- Always cite your sources when using information from financial documents

Think step by step and use the tools methodically to answer user queries accurately."""

    def _build_invoke_config(self, user_id: str) -> dict[str, Any]:
        """
        Build LangGraph invoke config with observability callbacks.

        Per Langfuse v3 docs:
        - CallbackHandler() takes no args (uses singleton Langfuse client)
        - Trace attributes are passed via config["metadata"] with langfuse_ prefix
        Per LangSmith docs:
        - Auto-traces via LANGCHAIN_TRACING_V2 env var, no callback needed
        """
        config: dict[str, Any] = {
            "metadata": {
                "langfuse_user_id": user_id,
                "langfuse_tags": ["agent_query"],
            },
        }

        if self._observability:
            callback = self._observability.get_langchain_callback()
            if callback is not None:
                config["callbacks"] = [callback]

        return config

    async def process_query(self, query: str, user_id: str) -> QueryResult:
        """
        Process a user query through the agent.

        Args:
            query: User's natural language query
            user_id: Unique identifier for the user making the query

        Returns:
            QueryResult with answer and reasoning steps

        Raises:
            ValueError: If query is invalid
            RuntimeError: If processing fails
        """
        if not query or not query.strip():
            logger.warning("Empty query received", extra={"user_id": user_id})
            raise ValueError("Query cannot be empty")

        logger.info("Processing agent query", extra={"query": query, "user_id": user_id})
        start_time = datetime.now()

        try:
            # Initialize state
            initial_state: AgentState = {
                "messages": [
                    SystemMessage(content=self._create_system_prompt()),
                    HumanMessage(content=query),
                ],
                "reasoning_steps": [],
                "final_answer": None,
            }

            # Build config with observability callbacks
            config = self._build_invoke_config(user_id)

            # Run the graph - callbacks handle all tracing automatically
            logger.info("Executing agent graph")
            final_state = await self._graph.ainvoke(initial_state, config=config)

            # Extract final answer
            last_message = final_state["messages"][-1]
            answer = (
                last_message.content
                if isinstance(last_message, AIMessage)
                else str(last_message)
            )

            # Convert reasoning steps to AgentStep entities
            reasoning_steps = []
            for idx, step in enumerate(final_state["reasoning_steps"], 1):
                reasoning_steps.append(
                    AgentStep(
                        step_number=idx,
                        action=step["action"],
                        action_input=step["action_input"],
                        observation="",
                        timestamp=step["timestamp"],
                    )
                )

            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            logger.info(
                "Agent query completed",
                extra={
                    "execution_time_ms": round(execution_time_ms, 2),
                    "reasoning_steps_count": len(reasoning_steps),
                },
            )

            # Flush observability data
            if self._observability:
                self._observability.flush()

            return QueryResult(
                query=query,
                answer=answer,
                reasoning_steps=reasoning_steps,
                sources=[],
                execution_time_ms=execution_time_ms,
                timestamp=datetime.now(),
                trace_id=None,
            )

        except Exception as e:
            logger.error(
                "Agent query failed",
                extra={"error": str(e), "query": query, "user_id": user_id},
                exc_info=True,
            )
            raise RuntimeError(f"Failed to process query: {str(e)}")

    async def process_query_stream(
        self, query: str, user_id: str
    ) -> AsyncIterator[StreamEvent]:
        """
        Process a user query through the agent with streaming events.

        Args:
            query: User's natural language query
            user_id: Unique identifier for the user making the query

        Yields:
            StreamEvent objects representing agent progress

        Raises:
            ValueError: If query is invalid
            RuntimeError: If processing fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        try:
            # Initialize state
            initial_state: AgentState = {
                "messages": [
                    SystemMessage(content=self._create_system_prompt()),
                    HumanMessage(content=query),
                ],
                "reasoning_steps": [],
                "final_answer": None,
            }

            # Build config with observability callbacks
            config = self._build_invoke_config(user_id)

            # Stream events from the graph
            event = None
            async for event in self._graph.astream(initial_state, config=config):
                for node_name, node_state in event.items():
                    if node_name == "agent":
                        yield StreamEvent(
                            event_type="agent_step",
                            data={"node": node_name, "state": "reasoning"},
                            timestamp=datetime.now(),
                        )

                        if node_state.get("messages"):
                            last_message = node_state["messages"][-1]
                            if (
                                hasattr(last_message, "tool_calls")
                                and last_message.tool_calls
                            ):
                                for tool_call in last_message.tool_calls:
                                    yield StreamEvent(
                                        event_type="tool_call",
                                        data={
                                            "tool": tool_call["name"],
                                            "args": tool_call["args"],
                                        },
                                        timestamp=datetime.now(),
                                    )

                    elif node_name == "tools":
                        yield StreamEvent(
                            event_type="tool_execution",
                            data={"node": node_name},
                            timestamp=datetime.now(),
                        )

            # Final answer
            if event is not None:
                last_message = list(event.values())[0]["messages"][-1]
                answer = (
                    last_message.content
                    if isinstance(last_message, AIMessage)
                    else str(last_message)
                )

                yield StreamEvent(
                    event_type="final_answer",
                    data={"answer": answer},
                    timestamp=datetime.now(),
                )

            # Flush observability data
            if self._observability:
                self._observability.flush()

        except Exception as e:
            yield StreamEvent(
                event_type="error",
                data={"error": str(e)},
                timestamp=datetime.now(),
            )
