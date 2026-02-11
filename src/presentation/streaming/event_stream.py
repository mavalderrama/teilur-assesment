"""Server-Sent Events streaming for agent responses."""
import json
from typing import Any, AsyncIterator

from src.domain.entities.query_result import StreamEvent


class EventStreamFormatter:
    """Formatter for Server-Sent Events (SSE)."""

    @staticmethod
    def format_event(event: StreamEvent) -> str:
        """
        Format a StreamEvent as an SSE message.

        Args:
            event: StreamEvent to format

        Returns:
            Formatted SSE message string
        """
        data = {
            "event_type": event.event_type,
            "data": event.data,
            "timestamp": event.timestamp.isoformat(),
        }

        return f"data: {json.dumps(data)}\n\n"

    @staticmethod
    async def stream_events(
        events: AsyncIterator[StreamEvent],
    ) -> AsyncIterator[str]:
        """
        Stream events in SSE format.

        Args:
            events: Async iterator of StreamEvent objects

        Yields:
            Formatted SSE messages
        """
        try:
            async for event in events:
                yield EventStreamFormatter.format_event(event)

        except Exception as e:
            # Send error event
            error_event = StreamEvent(
                event_type="error",
                data={"error": str(e)},
                timestamp=event.timestamp if 'event' in locals() else None,
            )
            yield EventStreamFormatter.format_event(error_event)

    @staticmethod
    def create_message_event(message: str) -> str:
        """
        Create a simple SSE message event.

        Args:
            message: Message text

        Returns:
            Formatted SSE message
        """
        return f"data: {json.dumps({'message': message})}\n\n"

    @staticmethod
    def create_done_event() -> str:
        """
        Create a done event to signal stream completion.

        Returns:
            Formatted SSE done message
        """
        return f"data: {json.dumps({'event_type': 'done'})}\n\n"
