"""Query result entity - represents the output of agent queries."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class AgentStep:
    """Represents a single step in agent reasoning."""

    step_number: int
    action: str
    action_input: dict[str, Any]
    observation: str
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if self.step_number < 1:
            raise ValueError("Step number must be positive")
        if not self.action:
            raise ValueError("Action cannot be empty")


@dataclass(frozen=True)
class QueryResult:
    """Represents the result of an agent query."""

    query: str
    answer: str
    reasoning_steps: list[AgentStep]
    sources: list[str]
    execution_time_ms: float
    timestamp: datetime
    trace_id: Optional[str] = None
    trace_url: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.query:
            raise ValueError("Query cannot be empty")
        if not self.answer:
            raise ValueError("Answer cannot be empty")
        if self.execution_time_ms < 0:
            raise ValueError("Execution time cannot be negative")


@dataclass
class StreamEvent:
    """Represents a streaming event from the agent."""

    event_type: str  # e.g., "agent_step", "tool_call", "final_answer"
    data: dict[str, Any]
    timestamp: datetime

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.event_type:
            raise ValueError("Event type cannot be empty")
        if self.data is None:
            raise ValueError("Event data cannot be None")
