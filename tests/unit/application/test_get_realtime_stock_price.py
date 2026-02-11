"""Unit tests for GetRealtimeStockPriceUseCase."""
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.use_cases.get_realtime_stock_price import (
    GetRealtimeStockPriceUseCase,
)
from src.domain.entities.stock_price import StockPrice
from src.domain.interfaces.stock_repository import IStockRepository


@pytest.fixture
def mock_stock_repository():
    """Create a mock stock repository."""
    return Mock(spec=IStockRepository)


@pytest.fixture
def use_case(mock_stock_repository):
    """Create use case with mocked repository."""
    return GetRealtimeStockPriceUseCase(stock_repository=mock_stock_repository)


class TestGetRealtimeStockPriceUseCase:
    """Tests for GetRealtimeStockPriceUseCase."""

    @pytest.mark.asyncio
    async def test_execute_with_valid_symbol(self, use_case, mock_stock_repository):
        """Test executing use case with valid symbol."""
        # Arrange
        expected_price = StockPrice(
            symbol="AMZN",
            price=Decimal("185.42"),
            timestamp=datetime.now(),
            currency="USD",
        )
        mock_stock_repository.get_realtime_price = AsyncMock(return_value=expected_price)

        # Act
        result = await use_case.execute("AMZN")

        # Assert
        assert result == expected_price
        mock_stock_repository.get_realtime_price.assert_called_once_with("AMZN")

    @pytest.mark.asyncio
    async def test_execute_normalizes_symbol_to_uppercase(
        self, use_case, mock_stock_repository
    ):
        """Test that symbol is normalized to uppercase."""
        # Arrange
        expected_price = StockPrice(
            symbol="AMZN",
            price=Decimal("185.42"),
            timestamp=datetime.now(),
        )
        mock_stock_repository.get_realtime_price = AsyncMock(return_value=expected_price)

        # Act
        await use_case.execute("amzn")  # lowercase

        # Assert
        mock_stock_repository.get_realtime_price.assert_called_once_with("AMZN")

    @pytest.mark.asyncio
    async def test_execute_strips_whitespace(self, use_case, mock_stock_repository):
        """Test that symbol whitespace is stripped."""
        # Arrange
        expected_price = StockPrice(
            symbol="AMZN",
            price=Decimal("185.42"),
            timestamp=datetime.now(),
        )
        mock_stock_repository.get_realtime_price = AsyncMock(return_value=expected_price)

        # Act
        await use_case.execute("  AMZN  ")

        # Assert
        mock_stock_repository.get_realtime_price.assert_called_once_with("AMZN")

    @pytest.mark.asyncio
    async def test_execute_with_empty_symbol_raises_error(self, use_case):
        """Test that empty symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol must be a non-empty string"):
            await use_case.execute("")

    @pytest.mark.asyncio
    async def test_execute_with_none_symbol_raises_error(self, use_case):
        """Test that None symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol must be a non-empty string"):
            await use_case.execute(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_execute_with_non_string_symbol_raises_error(self, use_case):
        """Test that non-string symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol must be a non-empty string"):
            await use_case.execute(123)  # type: ignore

    @pytest.mark.asyncio
    async def test_execute_propagates_repository_errors(
        self, use_case, mock_stock_repository
    ):
        """Test that repository errors are propagated."""
        # Arrange
        mock_stock_repository.get_realtime_price = AsyncMock(
            side_effect=RuntimeError("API connection failed")
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="API connection failed"):
            await use_case.execute("AMZN")
