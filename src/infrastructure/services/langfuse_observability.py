"""Langfuse observability service using v3 SDK."""
import uuid
from datetime import datetime
from typing import Any, Optional

from langfuse import Langfuse, get_client, propagate_attributes
from langfuse.langchain import CallbackHandler

from src.domain.interfaces.observability_service import IObservabilityService
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class LangfuseObservabilityService(IObservabilityService):
    """Service for Langfuse observability and tracing (v3 SDK).

    In v3, Langfuse uses a singleton client pattern:
    1. Initialize Langfuse(public_key=..., secret_key=...) once at startup
    2. CallbackHandler() uses the singleton - no credential args needed
    3. Trace metadata (user_id, tags) is passed via config["metadata"] with langfuse_ prefix
    """

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://us.cloud.langfuse.com",
    ) -> None:
        self._public_key = public_key
        self._secret_key = secret_key
        self._host = host
        self._last_handler = None

        # Initialize the Langfuse client
        self._langfuse = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )

        # Verify credentials
        try:
            auth_ok = self._langfuse.auth_check()
            logger.info(
                "Langfuse observability service initialized",
                extra={"host": host, "auth_check": auth_ok},
            )
        except Exception as e:
            logger.error(f"Langfuse auth check failed: {e}", extra={"host": host})

    def get_langchain_callback(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Get a Langfuse CallbackHandler for automatic LangChain/LangGraph tracing.

        In v3, CallbackHandler() takes no credential args — it uses the singleton
        Langfuse client initialized in __init__. Trace attributes (user_id, tags, etc.)
        are passed via config["metadata"] with langfuse_ prefix when invoking the graph.
        """
        try:
            handler = CallbackHandler(update_trace=True)
            self._last_handler = handler
            logger.info("Langfuse CallbackHandler created", extra={"user_id": user_id})
            return handler
        except Exception as e:
            logger.error(
                f"Failed to create Langfuse CallbackHandler: {e}",
                extra={"error": str(e)},
                exc_info=True,
            )
            return None

    @staticmethod
    def build_langfuse_metadata(
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Build metadata dict with langfuse_ prefixed keys for config["metadata"]."""
        meta: dict[str, Any] = {}
        if user_id:
            meta["langfuse_user_id"] = user_id
        if session_id:
            meta["langfuse_session_id"] = session_id
        if tags:
            meta["langfuse_tags"] = tags
        return meta

    def create_trace(
        self, name: str, user_id: Optional[str] = None, metadata: Optional[dict[str, Any]] = None
    ) -> str:
        trace_id = str(uuid.uuid4())

        with self._langfuse.start_as_current_span(
            name=name,
            input={"user_id": user_id},
            metadata=metadata or {},
        ) as span:
            if user_id:
                with propagate_attributes(user_id=user_id):
                    pass

        return trace_id

    def log_llm_generation(
        self,
        trace_id: str,
        name: str,
        model: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        with self._langfuse.start_as_current_observation(
            name=name,
            as_type="generation",
            model=model,
        ) as generation:
            generation.update(
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
        event_metadata = metadata or {}
        if error:
            event_metadata["error"] = error

        with self._langfuse.start_as_current_span(
            name=f"tool_{tool_name}",
            input=tool_input,
            metadata=event_metadata,
        ) as span:
            span.update(output=tool_output)

    def log_span(
        self,
        trace_id: str,
        name: str,
        start_time: datetime,
        end_time: datetime,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        with self._langfuse.start_as_current_span(
            name=name,
            metadata=metadata or {},
        ) as span:
            span.update(output={"duration_ms": (end_time - start_time).total_seconds() * 1000})

    def complete_trace(
        self,
        trace_id: str,
        outputs: Optional[dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        completion_metadata = {}
        if outputs:
            completion_metadata["outputs"] = outputs
        if error:
            completion_metadata["error"] = error

        if completion_metadata:
            with self._langfuse.start_as_current_span(
                name="trace_complete",
                metadata=completion_metadata,
            ) as span:
                span.update(output=completion_metadata)

    def get_trace_url(self, trace_id: str) -> Optional[str]:
        try:
            return self._langfuse.get_trace_url(trace_id=trace_id)
        except Exception:
            return None

    def flush(self) -> None:
        try:
            self._langfuse.flush()
            logger.info("Langfuse flushed")
        except Exception as e:
            logger.error(f"Langfuse flush failed: {e}")
