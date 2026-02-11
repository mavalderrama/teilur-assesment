"""Agent orchestrator interface - defines contract for AI agent coordination."""
from abc import ABC, abstractmethod
from typing import AsyncIterator

from src.domain.entities.query_result import QueryResult, StreamEvent


class IAgentOrchestrator(ABC):
    """Interface for AI agent orchestration."""

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
