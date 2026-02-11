"""LangGraph orchestrator implementation with ReAct pattern."""
from datetime import datetime
from typing import Any, AsyncIterator, TypedDict

from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from src.application.interfaces.agent_orchestrator import IAgentOrchestrator
from src.domain.entities.query_result import AgentStep, QueryResult, StreamEvent
from src.domain.interfaces.observability_service import IObservabilityService
from src.infrastructure.agent.tools import AgentTools


class AgentState(TypedDict):
    """State for the agent graph."""

    messages: list
    reasoning_steps: list[dict[str, Any]]
    final_answer: str | None
    trace_id: str | None


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
            llm_model_id: AWS Bedrock model ID
            region: AWS region
            agent_tools: Agent tools factory
            observability_service: Optional observability service (Langfuse or LangSmith)
        """
        self._llm = ChatBedrock(
            model_id=llm_model_id,
            region_name=region,
            model_kwargs={"temperature": 0.7, "max_tokens": 2048},
        )

        self._tools = agent_tools.create_tools()
        self._llm_with_tools = self._llm.bind_tools(self._tools)
        self._observability = observability_service

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """Build the LangGraph workflow."""
        # Create workflow
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(self._tools))

        # Define edges
        workflow.set_entry_point("agent")
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    async def _agent_node(self, state: AgentState) -> AgentState:
        """Agent reasoning node."""
        messages = state["messages"]
        response = await self._llm_with_tools.ainvoke(messages)

        # Update state
        state["messages"].append(response)

        # Track reasoning step
        if hasattr(response, "tool_calls") and response.tool_calls:
            for tool_call in response.tool_calls:
                state["reasoning_steps"].append(
                    {
                        "action": tool_call["name"],
                        "action_input": tool_call["args"],
                        "timestamp": datetime.now(),
                    }
                )

        return state

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue to tools or end."""
        last_message = state["messages"][-1]

        # If there are tool calls, continue to tools
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "continue"

        # Otherwise, we're done
        return "end"

    def _create_system_prompt(self) -> str:
        """Create system prompt for the agent."""
        return """You are a helpful financial AI agent specialized in stock market analysis and Amazon's financial information.

You have access to the following tools:
1. get_realtime_stock_price: Get current stock price for any ticker symbol
2. get_historical_stock_prices: Get historical price data over a date range
3. search_financial_documents: Search Amazon's financial documents (annual reports, quarterly earnings)

When answering questions:
- Use tools to gather factual, up-to-date information
- Provide clear, concise answers based on the retrieved data
- When comparing data, use the appropriate tools to get both pieces of information
- If you need historical data, remember that Q4 spans October-December
- Always cite your sources when using information from financial documents

Think step by step and use the tools methodically to answer user queries accurately."""

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
            raise ValueError("Query cannot be empty")

        start_time = datetime.now()
        trace_id = None

        try:
            # Create observability trace
            if self._observability:
                trace_id = self._observability.create_trace(
                    name="agent_query",
                    user_id=user_id,
                    metadata={"query": query},
                )

            # Initialize state
            initial_state: AgentState = {
                "messages": [
                    SystemMessage(content=self._create_system_prompt()),
                    HumanMessage(content=query),
                ],
                "reasoning_steps": [],
                "final_answer": None,
                "trace_id": trace_id,
            }

            # Run the graph
            final_state = await self._graph.ainvoke(initial_state)

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
                        observation="",  # Tool output captured separately
                        timestamp=step["timestamp"],
                    )
                )

            # Calculate execution time
            execution_time_ms = (
                datetime.now() - start_time
            ).total_seconds() * 1000

            # Log to observability service
            if self._observability and trace_id:
                self._observability.log_llm_generation(
                    trace_id=trace_id,
                    name="agent_response",
                    model=self._llm.model_id,
                    input_data=query,
                    output_data=answer,
                    metadata={"execution_time_ms": execution_time_ms},
                )

                # Complete the trace
                self._observability.complete_trace(
                    trace_id=trace_id,
                    outputs={"answer": answer, "execution_time_ms": execution_time_ms},
                )

            return QueryResult(
                query=query,
                answer=answer,
                reasoning_steps=reasoning_steps,
                sources=[],  # Would extract from tool calls
                execution_time_ms=execution_time_ms,
                timestamp=datetime.now(),
                trace_id=trace_id,
            )

        except Exception as e:
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
            # Create observability trace
            trace_id = None
            if self._observability:
                trace_id = self._observability.create_trace(
                    name="agent_query_stream",
                    user_id=user_id,
                    metadata={"query": query},
                )

            # Initialize state
            initial_state: AgentState = {
                "messages": [
                    SystemMessage(content=self._create_system_prompt()),
                    HumanMessage(content=query),
                ],
                "reasoning_steps": [],
                "final_answer": None,
                "trace_id": trace_id,
            }

            # Stream events from the graph
            async for event in self._graph.astream(initial_state):
                # Extract node name and state
                for node_name, node_state in event.items():
                    if node_name == "agent":
                        # Agent reasoning step
                        yield StreamEvent(
                            event_type="agent_step",
                            data={"node": node_name, "state": "reasoning"},
                            timestamp=datetime.now(),
                        )

                        # Check for tool calls
                        if node_state["messages"]:
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
                        # Tool execution
                        yield StreamEvent(
                            event_type="tool_execution",
                            data={"node": node_name},
                            timestamp=datetime.now(),
                        )

            # Final answer
            final_state = event
            last_message = list(final_state.values())[0]["messages"][-1]
            answer = (
                last_message.content
                if isinstance(last_message, AIMessage)
                else str(last_message)
            )

            yield StreamEvent(
                event_type="final_answer",
                data={"answer": answer, "trace_id": trace_id},
                timestamp=datetime.now(),
            )

        except Exception as e:
            yield StreamEvent(
                event_type="error",
                data={"error": str(e)},
                timestamp=datetime.now(),
            )
