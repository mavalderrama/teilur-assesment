"""Langfuse observability service."""
from datetime import datetime
from typing import Any, Optional

from langfuse import Langfuse
from langfuse.decorators import langfuse_context, observe

from src.domain.interfaces.observability_service import IObservabilityService


class LangfuseObservabilityService(IObservabilityService):
    """Service for Langfuse observability and tracing."""

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
    ) -> None:
        """
        Initialize Langfuse observability service.

        Args:
            public_key: Langfuse public API key
            secret_key: Langfuse secret API key
            host: Langfuse host URL
        """
        self._langfuse = Langfuse(
            public_key=public_key, secret_key=secret_key, host=host
        )

    def create_trace(
        self, name: str, user_id: Optional[str] = None, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Create a new trace in Langfuse.

        Args:
            name: Trace name
            user_id: Optional user identifier
            metadata: Optional trace metadata

        Returns:
            Trace ID
        """
        trace = self._langfuse.trace(
            name=name, user_id=user_id, metadata=metadata or {}
        )
        return str(trace.id) if hasattr(trace, 'id') else ""

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
        Log an LLM generation to Langfuse.

        Args:
            trace_id: Parent trace ID
            name: Generation name
            model: Model identifier
            input_data: Input to the model
            output_data: Output from the model
            metadata: Optional generation metadata
        """
        self._langfuse.generation(
            trace_id=trace_id,
            name=name,
            model=model,
            input=input_data,
            output=output_data,
            metadata=metadata or {},
        )

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
        Log a tool execution to Langfuse.

        Args:
            trace_id: Parent trace ID
            tool_name: Name of the tool
            tool_input: Tool input parameters
            tool_output: Tool output/result
            error: Optional error message
            metadata: Optional metadata
        """
        event_metadata = metadata or {}
        event_metadata.update({
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
        })
        if error:
            event_metadata["error"] = error

        self._langfuse.event(
            trace_id=trace_id,
            name=f"tool_{tool_name}",
            metadata=event_metadata,
        )

    def log_span(
        self,
        trace_id: str,
        name: str,
        start_time: datetime,
        end_time: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """
        Log a span (time-bounded operation) to Langfuse.

        Args:
            trace_id: Parent trace ID
            name: Span name
            start_time: Span start time
            end_time: Span end time
            metadata: Optional span metadata
        """
        self._langfuse.span(
            trace_id=trace_id,
            name=name,
            start_time=start_time,
            end_time=end_time,
            metadata=metadata or {},
        )

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
        # Langfuse traces are auto-completed, but we can log final event
        if outputs or error:
            event_metadata = {}
            if outputs:
                event_metadata["outputs"] = outputs
            if error:
                event_metadata["error"] = error

            self._langfuse.event(
                trace_id=trace_id,
                name="trace_complete",
                metadata=event_metadata,
            )

    def get_trace_url(self, trace_id: str) -> Optional[str]:
        """
        Get the URL for viewing a trace.

        Args:
            trace_id: Trace ID

        Returns:
            URL to view the trace, or None if not available
        """
        # Use the static method from langfuse_context
        return langfuse_context.get_current_trace_url()

    def flush(self) -> None:
        """Flush pending traces to Langfuse."""
        self._langfuse.flush()

    @staticmethod
    def observe_function(name: str | None = None) -> Any:
        """
        Decorator to automatically trace a function with Langfuse.

        Args:
            name: Optional custom name for the observation

        Returns:
            Decorator function
        """
        return observe(name=name)

    @staticmethod
    def get_trace_url() -> str | None:
        """
        Get the URL for the current trace.

        Returns:
            Trace URL if available, None otherwise
        """
        return langfuse_context.get_current_trace_url()
