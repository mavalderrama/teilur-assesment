"""End-to-end integration tests for the agent."""
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.use_cases.get_historical_stock_price import (
    GetHistoricalStockPriceUseCase,
)
from src.application.use_cases.get_realtime_stock_price import (
    GetRealtimeStockPriceUseCase,
)
from src.application.use_cases.query_documents import QueryDocumentsUseCase
from src.domain.interfaces.observability_service import IObservabilityService
from src.infrastructure.agent.langgraph_orchestrator import LangGraphOrchestrator
from src.infrastructure.agent.tools import AgentTools
from src.infrastructure.repositories.yfinance_stock_repository import (
    YFinanceStockRepository,
)


@pytest.mark.integration
@pytest.mark.slow
class TestAgentEndToEnd:
    """End-to-end integration tests for the agent system."""

    @pytest.fixture
    def stock_repository(self):
        """Create real stock repository."""
        return YFinanceStockRepository()

    @pytest.fixture
    def mock_document_repository(self):
        """Create mock document repository (requires Bedrock)."""
        from src.domain.interfaces.document_repository import IDocumentRepository

        mock = Mock(spec=IDocumentRepository)
        mock.search_documents = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_observability(self):
        """Create mock observability service."""
        mock = Mock(spec=IObservabilityService)
        mock.create_trace = Mock(return_value="trace_123")
        mock.log_llm_generation = Mock()
        mock.log_tool_execution = Mock()
        mock.complete_trace = Mock()
        mock.get_trace_url = Mock(return_value="https://example.com/trace/123")
        mock.flush = Mock()
        return mock

    @pytest.fixture
    def agent_tools(self, stock_repository, mock_document_repository):
        """Create agent tools with real and mocked dependencies."""
        return AgentTools(
            get_realtime_price_uc=GetRealtimeStockPriceUseCase(stock_repository),
            get_historical_price_uc=GetHistoricalStockPriceUseCase(stock_repository),
            query_documents_uc=QueryDocumentsUseCase(mock_document_repository),
        )

    @pytest.fixture
    def orchestrator(self, agent_tools, mock_observability):
        """Create LangGraph orchestrator with real tools."""
        # Note: This requires AWS Bedrock access
        # Skip if AWS credentials not available
        import os

        if not os.getenv("AWS_ACCESS_KEY_ID"):
            pytest.skip("AWS credentials not available")

        return LangGraphOrchestrator(
            llm_model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            region="us-east-1",
            agent_tools=agent_tools,
            observability_service=mock_observability,
        )

    @pytest.mark.asyncio
    async def test_agent_answers_stock_price_query(self, orchestrator):
        """Test that agent can answer stock price query end-to-end."""
        # This test requires AWS Bedrock access and may be slow
        pytest.skip("Requires AWS Bedrock access - enable manually for E2E testing")

        # Act
        result = await orchestrator.process_query(
            query="What is the current stock price for Amazon?",
            user_id="test_user",
        )

        # Assert
        assert result.query == "What is the current stock price for Amazon?"
        assert "AMZN" in result.answer or "Amazon" in result.answer
        assert "$" in result.answer  # Should mention price in dollars
        assert len(result.reasoning_steps) > 0
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_agent_uses_correct_tool_for_realtime_price(self, agent_tools):
        """Test that agent tools work correctly for realtime price."""
        # Arrange
        tools = agent_tools.create_tools()
        realtime_tool = tools[0]  # get_realtime_stock_price

        # Act
        result = await realtime_tool.ainvoke({"symbol": "AMZN"})

        # Assert
        assert "AMZN" in result
        assert "Current Price" in result or "Price" in result
        assert "$" in result

    @pytest.mark.asyncio
    async def test_agent_uses_correct_tool_for_historical_price(self, agent_tools):
        """Test that agent tools work correctly for historical price."""
        # Arrange
        tools = agent_tools.create_tools()
        historical_tool = tools[1]  # get_historical_stock_prices

        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Act
        result = await historical_tool.ainvoke({
            "symbol": "AMZN",
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "period": "1d",
        })

        # Assert
        assert "AMZN" in result
        assert "Historical" in result or "Average" in result
        assert "$" in result

    @pytest.mark.asyncio
    async def test_streaming_query_yields_events(self, orchestrator):
        """Test that streaming query yields events."""
        # This test requires AWS Bedrock access
        pytest.skip("Requires AWS Bedrock access - enable manually for E2E testing")

        # Act
        events = []
        async for event in orchestrator.process_query_stream(
            query="What is AMZN stock price?",
            user_id="test_user",
        ):
            events.append(event)

        # Assert
        assert len(events) > 0
        event_types = [e.event_type for e in events]
        assert "final_answer" in event_types
