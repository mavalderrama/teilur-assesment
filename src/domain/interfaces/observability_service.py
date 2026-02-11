"""Observability service interface - defines contract for tracing and logging."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Optional


class IObservabilityService(ABC):
    """Interface for observability and tracing services."""

    @abstractmethod
    def create_trace(
        self, name: str, user_id: Optional[str] = None, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Create a new trace.

        Args:
            name: Trace name
            user_id: Optional user identifier
            metadata: Optional trace metadata

        Returns:
            Trace ID
        """
        pass

    @abstractmethod
    def log_llm_generation(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log an LLM generation.

        Args:
            trace_id: Parent trace ID
            name: Generation name
            model: Model identifier
            input_data: Input to the model
            output_data: Output from the model
            metadata: Optional metadata
        """
        pass

    @abstractmethod
    def log_tool_execution(
        self,
        trace_id: str,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: str,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log a tool execution.

        Args:
            trace_id: Parent trace ID
            tool_name: Name of the tool
            tool_input: Tool input parameters
            tool_output: Tool output/result
            error: Optional error message
            metadata: Optional metadata
        """
        pass

    @abstractmethod
    def log_span(
        self,
        trace_id: str,
        name: str,
        start_time: datetime,
        end_time: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log a span (time-bounded operation).

        Args:
            trace_id: Parent trace ID
            name: Span name
            start_time: Span start time
            end_time: Span end time
            metadata: Optional metadata
        """
        pass

    @abstractmethod
    def complete_trace(
        self,
        trace_id: str,
        outputs: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        Complete a trace with final outputs or error.

        Args:
            trace_id: Trace ID to complete
            outputs: Optional output data
            error: Optional error message
        """
        pass

    @abstractmethod
    def get_trace_url(self, trace_id: str) -> Optional[str]:
        """
        Get the URL for viewing a trace.

        Args:
            trace_id: Trace ID

        Returns:
            URL to view the trace, or None if not available
        """
        pass

    @abstractmethod
    def flush(self) -> None:
        """Flush pending traces to the observability backend."""
        pass
