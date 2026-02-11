"""LangSmith observability service."""
import os
from datetime import datetime
from typing import Any, Optional

from langsmith import Client

from src.domain.interfaces.observability_service import IObservabilityService


class LangSmithObservabilityService(IObservabilityService):
    """Service for LangSmith observability and tracing."""

    def __init__(
        self,
        api_key: str,
        project_name: str = "aws-ai-agent",
        endpoint: str = "https://api.smith.langchain.com",
    ) -> None:
        """
        Initialize LangSmith observability service.

        Args:
            api_key: LangSmith API key
            project_name: Project name for organizing traces
            endpoint: LangSmith API endpoint
        """
        self._api_key = api_key
        self._project_name = project_name
        self._endpoint = endpoint

        # Set environment variables for LangSmith SDK
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project_name
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint

        # Initialize LangSmith client
        self._client = Client(api_key=api_key, api_url=endpoint)

    def create_trace(
        self, name: str, user_id: Optional[str] = None, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        """
        Create a new trace in LangSmith.

        Args:
            name: Trace name
            user_id: Optional user identifier
            metadata: Optional trace metadata

        Returns:
            Trace ID
        """
        trace_metadata = metadata or {}
        if user_id:
            trace_metadata["user_id"] = user_id

        run = self._client.create_run(
            name=name,
            run_type="chain",
            inputs={},
            project_name=self._project_name,
            tags=["trace"],
            extra=trace_metadata,
        )
        return str(run.id)

    def _create_run(
        self,
        name: str,
        run_type: str,
        inputs: dict[str, Any],
        parent_run_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Internal helper to create a run in LangSmith.

        Args:
            name: Run name
            run_type: Type of run (e.g., "chain", "llm", "tool")
            inputs: Input data for the run
            parent_run_id: Optional parent run ID for nested runs
            tags: Optional list of tags
            metadata: Optional metadata dictionary

        Returns:
            Run ID
        """
        run = self._client.create_run(
            name=name,
            run_type=run_type,
            inputs=inputs,
            project_name=self._project_name,
            parent_run_id=parent_run_id,
            tags=tags or [],
            extra=metadata or {},
        )
        return str(run.id)

    def _update_run(
        self,
        run_id: str,
        outputs: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
        end_time: Optional[datetime] = None,
    ) -> None:
        """
        Internal helper to update an existing run.

        Args:
            run_id: Run ID to update
            outputs: Optional output data
            error: Optional error message if run failed
            end_time: Optional end timestamp
        """
        self._client.update_run(
            run_id=run_id,
            outputs=outputs,
            error=error,
            end_time=end_time,
        )

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
        Log an LLM generation run.

        Args:
            trace_id: Parent trace ID
            name: Run name
            model: Model identifier
            input_data: Input prompt
            output_data: Generated completion
            metadata: Optional metadata
        """
        run_metadata = metadata or {}
        run_metadata["model"] = model

        run_id = self._create_run(
            name=name,
            run_type="llm",
            inputs={"input": input_data},
            parent_run_id=trace_id,
            metadata=run_metadata,
        )
        self._update_run(run_id=run_id, outputs={"output": output_data})

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
        Log a tool execution run.

        Args:
            trace_id: Parent trace ID
            tool_name: Name of the tool
            tool_input: Tool input parameters
            tool_output: Tool output/result
            error: Optional error message
            metadata: Optional metadata
        """
        run_metadata = metadata or {}
        run_metadata["tool_name"] = tool_name

        run_id = self._create_run(
            name=f"tool_{tool_name}",
            run_type="tool",
            inputs={"tool": tool_name, "input": tool_input},
            parent_run_id=trace_id,
            metadata=run_metadata,
        )

        outputs = {"output": tool_output} if not error else {}
        self._update_run(run_id=run_id, outputs=outputs, error=error)

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
        run_id = self._create_run(
            name=name,
            run_type="chain",
            inputs={},
            parent_run_id=trace_id,
            metadata=metadata,
        )
        self._update_run(run_id=run_id, outputs={}, end_time=end_time)

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
        self._update_run(run_id=trace_id, outputs=outputs, error=error)

    def get_trace_url(self, trace_id: str) -> Optional[str]:
        """
        Get the URL for viewing a trace in LangSmith UI.

        Args:
            trace_id: Trace ID

        Returns:
            URL to view the trace
        """
        return f"{self._endpoint}/o/default/projects/p/{self._project_name}/r/{trace_id}"

    def flush(self) -> None:
        """Flush pending traces (no-op for LangSmith as it's synchronous)."""
        pass

