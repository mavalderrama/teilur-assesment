"""LangSmith observability service."""
import os
from datetime import datetime
from typing import Any, Optional

from langsmith import Client

from src.domain.interfaces.observability_service import IObservabilityService
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class LangSmithObservabilityService(IObservabilityService):
    """Service for LangSmith observability and tracing."""

    def __init__(
        self,
        api_key: str,
        project_name: str = "aws-ai-agent",
        endpoint: str = "https://api.smith.langchain.com",
    ) -> None:
        self._api_key = api_key
        self._project_name = project_name
        self._endpoint = endpoint

        # Set environment variables for LangSmith auto-tracing
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = api_key
        os.environ["LANGCHAIN_PROJECT"] = project_name
        os.environ["LANGCHAIN_ENDPOINT"] = endpoint

        self._client = Client(api_key=api_key, api_url=endpoint)

        logger.info(
            "LangSmith observability service initialized",
            extra={"project": project_name, "endpoint": endpoint},
        )

    def get_langchain_callback(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        """
        LangSmith auto-traces via env vars (LANGCHAIN_TRACING_V2=true).

        Returns None since no explicit callback is needed. The orchestrator
        handles this by only adding non-None callbacks to the config.
        """
        return None

    def create_trace(
        self, name: str, user_id: Optional[str] = None, metadata: Optional[dict[str, Any]] = None
    ) -> str:
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

    def log_llm_generation(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
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
        self._update_run(run_id=trace_id, outputs=outputs, error=error)

    def get_trace_url(self, trace_id: str) -> Optional[str]:
        return f"{self._endpoint}/o/default/projects/p/{self._project_name}/r/{trace_id}"

    def flush(self) -> None:
        """Flush pending traces (no-op for LangSmith as it's synchronous)."""
        pass

    def _create_run(
        self,
        name: str,
        run_type: str,
        inputs: dict[str, Any],
        parent_run_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str:
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
        self._client.update_run(
            run_id=run_id,
            outputs=outputs,
            error=error,
            end_time=end_time,
        )
