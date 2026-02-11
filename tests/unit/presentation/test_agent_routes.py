"""Unit tests for agent API routes."""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.domain.entities.query_result import AgentStep, QueryResult, StreamEvent
from src.presentation.api.routes.agent import router


@pytest.mark.unit
class TestAgentRoutes:
    """Unit tests for agent API routes."""

    @pytest.fixture
    def mock_orchestrator(self):
        """Create mock orchestrator."""
        mock = Mock()
        mock.process_query = AsyncMock()
        mock.process_query_stream = Mock()
        return mock

    @pytest.fixture
    def app(self, mock_orchestrator):
        """Create FastAPI test app with mocked dependencies."""
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)

        # Override dependency
        from src.application.interfaces.agent_orchestrator import IAgentOrchestrator

        def get_mock_orchestrator():
            return mock_orchestrator

        app.dependency_overrides[IAgentOrchestrator] = get_mock_orchestrator

        # Override auth dependency
        from src.presentation.api.middleware.auth_middleware import get_user_id

        def get_mock_user_id():
            return "test_user_123"

        app.dependency_overrides[get_user_id] = get_mock_user_id

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_query_agent_non_streaming_returns_query_response(
        self, client, mock_orchestrator
    ):
        """Test that non-streaming query returns QueryResponse."""
        # Arrange
        mock_result = QueryResult(
            query="What is AMZN stock price?",
            answer="AMZN is currently trading at $185.42",
            reasoning_steps=[
                AgentStep(
                    step_number=1,
                    action="get_realtime_stock_price",
                    action_input={"symbol": "AMZN"},
                    observation="Current price: $185.42",
                    timestamp=datetime.now(),
                )
            ],
            sources=["yfinance API"],
            execution_time_ms=1234,
            timestamp=datetime.now(),
            trace_id="trace_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "What is AMZN stock price?", "stream": False},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "What is AMZN stock price?"
        assert data["answer"] == "AMZN is currently trading at $185.42"
        assert len(data["reasoning_steps"]) == 1
        assert data["reasoning_steps"][0]["action"] == "get_realtime_stock_price"
        assert data["execution_time_ms"] == 1234
        assert data["trace_id"] == "trace_123"

    def test_query_agent_streaming_returns_streaming_response(self, client, mock_orchestrator):
        """Test that streaming query returns StreamingResponse."""
        # Arrange
        async def mock_stream():
            yield StreamEvent(
                event_type="step",
                data={
                    "step_number": 1,
                    "action": "get_realtime_stock_price",
                    "action_input": {"symbol": "AMZN"},
                },
                timestamp=datetime.now(),
            )
            yield StreamEvent(
                event_type="final_answer",
                data={"answer": "AMZN is currently trading at $185.42"},
                timestamp=datetime.now(),
            )

        mock_orchestrator.process_query_stream.return_value = mock_stream()

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "What is AMZN stock price?", "stream": True},
        )

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert response.headers["cache-control"] == "no-cache"

    def test_query_agent_calls_orchestrator_with_correct_params(
        self, client, mock_orchestrator
    ):
        """Test that orchestrator is called with correct parameters."""
        # Arrange
        mock_result = QueryResult(
            query="test query",
            answer="test answer",
            reasoning_steps=[],
            sources=[],
            execution_time_ms=100,
            timestamp=datetime.now(),
            trace_id="trace_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act
        client.post(
            "/agent/query",
            json={"query": "test query", "stream": False},
        )

        # Assert
        mock_orchestrator.process_query.assert_called_once_with("test query", "test_user_123")

    def test_query_agent_raises_400_on_value_error(self, client, mock_orchestrator):
        """Test that ValueError raises 400 Bad Request."""
        # Arrange
        mock_orchestrator.process_query.side_effect = ValueError("Invalid query")

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "", "stream": False},
        )

        # Assert
        assert response.status_code == 400
        assert "Invalid query" in response.json()["detail"]

    def test_query_agent_raises_500_on_internal_error(self, client, mock_orchestrator):
        """Test that unexpected exceptions raise 500 Internal Server Error."""
        # Arrange
        mock_orchestrator.process_query.side_effect = RuntimeError("Database connection failed")

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "test query", "stream": False},
        )

        # Assert
        assert response.status_code == 500
        assert "Internal server error" in response.json()["detail"]

    def test_query_agent_validates_request_schema(self, client):
        """Test that invalid request schema is rejected."""
        # Act - Missing required 'query' field
        response = client.post(
            "/agent/query",
            json={"stream": False},
        )

        # Assert
        assert response.status_code == 422  # Unprocessable Entity

    def test_query_agent_default_stream_is_false(self, client, mock_orchestrator):
        """Test that stream defaults to False if not provided."""
        # Arrange
        mock_result = QueryResult(
            query="test",
            answer="answer",
            reasoning_steps=[],
            sources=[],
            execution_time_ms=100,
            timestamp=datetime.now(),
            trace_id="trace_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act - No stream field in request
        response = client.post(
            "/agent/query",
            json={"query": "test query"},
        )

        # Assert
        assert response.status_code == 200
        # Should call process_query (non-streaming)
        mock_orchestrator.process_query.assert_called_once()

    def test_query_agent_converts_reasoning_steps_correctly(self, client, mock_orchestrator):
        """Test that AgentStep entities are converted to AgentStepResponse."""
        # Arrange
        timestamp = datetime.now()
        mock_result = QueryResult(
            query="test",
            answer="answer",
            reasoning_steps=[
                AgentStep(
                    step_number=1,
                    action="action1",
                    action_input={"param": "value"},
                    observation="observation1",
                    timestamp=timestamp,
                ),
                AgentStep(
                    step_number=2,
                    action="action2",
                    action_input={},
                    observation="observation2",
                    timestamp=timestamp,
                ),
            ],
            sources=["source1"],
            execution_time_ms=200,
            timestamp=timestamp,
            trace_id="trace_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "test query", "stream": False},
        )

        # Assert
        data = response.json()
        assert len(data["reasoning_steps"]) == 2
        assert data["reasoning_steps"][0]["step_number"] == 1
        assert data["reasoning_steps"][0]["action"] == "action1"
        assert data["reasoning_steps"][1]["step_number"] == 2
        assert data["reasoning_steps"][1]["action"] == "action2"

    def test_query_agent_includes_sources_in_response(self, client, mock_orchestrator):
        """Test that sources are included in the response."""
        # Arrange
        mock_result = QueryResult(
            query="test",
            answer="answer",
            reasoning_steps=[],
            sources=["yfinance API", "Amazon 2024 Annual Report"],
            execution_time_ms=100,
            timestamp=datetime.now(),
            trace_id="trace_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "test query", "stream": False},
        )

        # Assert
        data = response.json()
        assert len(data["sources"]) == 2
        assert "yfinance API" in data["sources"]
        assert "Amazon 2024 Annual Report" in data["sources"]

    def test_query_agent_includes_trace_id_when_present(self, client, mock_orchestrator):
        """Test that trace_id is included when provided by orchestrator."""
        # Arrange
        mock_result = QueryResult(
            query="test",
            answer="answer",
            reasoning_steps=[],
            sources=[],
            execution_time_ms=100,
            timestamp=datetime.now(),
            trace_id="custom_trace_id_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "test query", "stream": False},
        )

        # Assert
        data = response.json()
        assert data["trace_id"] == "custom_trace_id_123"

    def test_query_agent_includes_execution_time(self, client, mock_orchestrator):
        """Test that execution_time_ms is included in response."""
        # Arrange
        mock_result = QueryResult(
            query="test",
            answer="answer",
            reasoning_steps=[],
            sources=[],
            execution_time_ms=5678,
            timestamp=datetime.now(),
            trace_id="trace_123",
        )
        mock_orchestrator.process_query.return_value = mock_result

        # Act
        response = client.post(
            "/agent/query",
            json={"query": "test query", "stream": False},
        )

        # Assert
        data = response.json()
        assert data["execution_time_ms"] == 5678
