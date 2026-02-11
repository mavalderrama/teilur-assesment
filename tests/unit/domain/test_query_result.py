"""Unit tests for QueryResult entities."""
from datetime import datetime

import pytest

from src.domain.entities.query_result import AgentStep, QueryResult, StreamEvent


class TestAgentStep:
    """Tests for AgentStep entity."""

    def test_create_valid_agent_step(self):
        """Test creating a valid AgentStep entity."""
        step = AgentStep(
            step_number=1,
            action="get_realtime_stock_price",
            action_input={"symbol": "AMZN"},
            observation="Stock price: $185.42",
            timestamp=datetime.now(),
        )

        assert step.step_number == 1
        assert step.action == "get_realtime_stock_price"
        assert step.action_input == {"symbol": "AMZN"}
        assert step.observation == "Stock price: $185.42"

    def test_invalid_step_number_raises_error(self):
        """Test that step_number < 1 raises ValueError."""
        with pytest.raises(ValueError, match="Step number must be positive"):
            AgentStep(
                step_number=0,
                action="test_action",
                action_input={},
                observation="observation",
                timestamp=datetime.now(),
            )

    def test_empty_action_raises_error(self):
        """Test that empty action raises ValueError."""
        with pytest.raises(ValueError, match="Action cannot be empty"):
            AgentStep(
                step_number=1,
                action="",
                action_input={},
                observation="observation",
                timestamp=datetime.now(),
            )


class TestQueryResult:
    """Tests for QueryResult entity."""

    def test_create_valid_query_result(self):
        """Test creating a valid QueryResult entity."""
        steps = [
            AgentStep(
                step_number=1,
                action="get_realtime_stock_price",
                action_input={"symbol": "AMZN"},
                observation="Price: $185.42",
                timestamp=datetime.now(),
            )
        ]

        result = QueryResult(
            query="What is AMZN stock price?",
            answer="Amazon's current stock price is $185.42",
            reasoning_steps=steps,
            sources=["yfinance"],
            execution_time_ms=1500.0,
            timestamp=datetime.now(),
            trace_id="trace_123",
        )

        assert result.query == "What is AMZN stock price?"
        assert result.answer == "Amazon's current stock price is $185.42"
        assert len(result.reasoning_steps) == 1
        assert result.sources == ["yfinance"]
        assert result.execution_time_ms == 1500.0
        assert result.trace_id == "trace_123"

    def test_empty_query_raises_error(self):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            QueryResult(
                query="",
                answer="Answer",
                reasoning_steps=[],
                sources=[],
                execution_time_ms=1000.0,
                timestamp=datetime.now(),
            )

    def test_empty_answer_raises_error(self):
        """Test that empty answer raises ValueError."""
        with pytest.raises(ValueError, match="Answer cannot be empty"):
            QueryResult(
                query="What is AMZN price?",
                answer="",
                reasoning_steps=[],
                sources=[],
                execution_time_ms=1000.0,
                timestamp=datetime.now(),
            )

    def test_negative_execution_time_raises_error(self):
        """Test that negative execution time raises ValueError."""
        with pytest.raises(ValueError, match="Execution time cannot be negative"):
            QueryResult(
                query="What is AMZN price?",
                answer="Answer",
                reasoning_steps=[],
                sources=[],
                execution_time_ms=-100.0,
                timestamp=datetime.now(),
            )


class TestStreamEvent:
    """Tests for StreamEvent entity."""

    def test_create_valid_stream_event(self):
        """Test creating a valid StreamEvent entity."""
        event = StreamEvent(
            event_type="tool_call",
            data={"tool": "get_realtime_stock_price", "args": {"symbol": "AMZN"}},
            timestamp=datetime.now(),
        )

        assert event.event_type == "tool_call"
        assert event.data["tool"] == "get_realtime_stock_price"
        assert event.data["args"]["symbol"] == "AMZN"

    def test_empty_event_type_raises_error(self):
        """Test that empty event_type raises ValueError."""
        with pytest.raises(ValueError, match="Event type cannot be empty"):
            StreamEvent(
                event_type="",
                data={"test": "data"},
                timestamp=datetime.now(),
            )

    def test_none_data_raises_error(self):
        """Test that None data raises ValueError."""
        with pytest.raises(ValueError, match="Event data cannot be None"):
            StreamEvent(
                event_type="test",
                data=None,  # type: ignore
                timestamp=datetime.now(),
            )

    def test_event_is_mutable(self):
        """Test that StreamEvent is mutable (not frozen)."""
        event = StreamEvent(
            event_type="test",
            data={"key": "value"},
            timestamp=datetime.now(),
        )

        # Should be able to modify (not frozen)
        event.data["new_key"] = "new_value"
        assert event.data["new_key"] == "new_value"
