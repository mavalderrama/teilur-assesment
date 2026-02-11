"""Unit tests for GetHistoricalStockPriceUseCase."""
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.use_cases.get_historical_stock_price import (
    GetHistoricalStockPriceUseCase,
)
from src.domain.entities.stock_price import HistoricalStockPrice, StockPrice
from src.domain.interfaces.stock_repository import IStockRepository


@pytest.fixture
def mock_stock_repository():
    """Create a mock stock repository."""
    return Mock(spec=IStockRepository)


@pytest.fixture
def use_case(mock_stock_repository):
    """Create use case with mocked repository."""
    return GetHistoricalStockPriceUseCase(stock_repository=mock_stock_repository)


class TestGetHistoricalStockPriceUseCase:
    """Tests for GetHistoricalStockPriceUseCase."""

    @pytest.mark.asyncio
    async def test_execute_with_valid_inputs(self, use_case, mock_stock_repository):
        """Test executing use case with valid inputs."""
        # Arrange
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        prices = [
            StockPrice(symbol="AMZN", price=Decimal("180.00"), timestamp=start_date),
            StockPrice(symbol="AMZN", price=Decimal("185.00"), timestamp=end_date),
        ]
        expected_result = HistoricalStockPrice(
            symbol="AMZN",
            start_date=start_date,
            end_date=end_date,
            prices=prices,
            period="1d",
        )
        mock_stock_repository.get_historical_prices = AsyncMock(return_value=expected_result)

        # Act
        result = await use_case.execute("AMZN", start_date, end_date, "1d")

        # Assert
        assert result == expected_result
        mock_stock_repository.get_historical_prices.assert_called_once_with(
            "AMZN", start_date, end_date, "1d"
        )

    @pytest.mark.asyncio
    async def test_execute_normalizes_symbol(self, use_case, mock_stock_repository):
        """Test that symbol is normalized to uppercase."""
        # Arrange
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        mock_stock_repository.get_historical_prices = AsyncMock(
            return_value=HistoricalStockPrice(
                symbol="AMZN",
                start_date=start_date,
                end_date=end_date,
                prices=[
                    StockPrice(symbol="AMZN", price=Decimal("180"), timestamp=start_date)
                ],
                period="1d",
            )
        )

        # Act
        await use_case.execute("amzn", start_date, end_date)

        # Assert
        mock_stock_repository.get_historical_prices.assert_called_once()
        call_args = mock_stock_repository.get_historical_prices.call_args[0]
        assert call_args[0] == "AMZN"

    @pytest.mark.asyncio
    async def test_execute_with_empty_symbol_raises_error(self, use_case):
        """Test that empty symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol must be a non-empty string"):
            await use_case.execute("", datetime.now(), datetime.now())

    @pytest.mark.asyncio
    async def test_execute_with_invalid_date_type_raises_error(self, use_case):
        """Test that non-datetime dates raise ValueError."""
        with pytest.raises(ValueError, match="Start date must be a datetime object"):
            await use_case.execute("AMZN", "2024-01-01", datetime.now())  # type: ignore

        with pytest.raises(ValueError, match="End date must be a datetime object"):
            await use_case.execute("AMZN", datetime.now(), "2024-01-31")  # type: ignore

    @pytest.mark.asyncio
    async def test_execute_with_start_after_end_raises_error(self, use_case):
        """Test that start_date >= end_date raises ValueError."""
        start_date = datetime(2024, 1, 31)
        end_date = datetime(2024, 1, 1)

        with pytest.raises(ValueError, match="Start date must be before end date"):
            await use_case.execute("AMZN", start_date, end_date)

    @pytest.mark.asyncio
    async def test_execute_with_equal_dates_raises_error(self, use_case):
        """Test that start_date == end_date raises ValueError."""
        same_date = datetime(2024, 1, 15)

        with pytest.raises(ValueError, match="Start date must be before end date"):
            await use_case.execute("AMZN", same_date, same_date)

    @pytest.mark.asyncio
    async def test_execute_with_invalid_period_raises_error(self, use_case):
        """Test that invalid period raises ValueError."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)

        with pytest.raises(ValueError, match="Period must be one of: 1d, 1wk, 1mo"):
            await use_case.execute("AMZN", start_date, end_date, "invalid")

    @pytest.mark.asyncio
    async def test_execute_with_valid_periods(self, use_case, mock_stock_repository):
        """Test that all valid periods are accepted."""
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 31)
        mock_result = HistoricalStockPrice(
            symbol="AMZN",
            start_date=start_date,
            end_date=end_date,
            prices=[StockPrice(symbol="AMZN", price=Decimal("180"), timestamp=start_date)],
            period="1d",
        )
        mock_stock_repository.get_historical_prices = AsyncMock(return_value=mock_result)

        # Test each valid period
        for period in ["1d", "1wk", "1mo"]:
            await use_case.execute("AMZN", start_date, end_date, period)
            # Should not raise error

    @pytest.mark.asyncio
    async def test_execute_propagates_repository_errors(
        self, use_case, mock_stock_repository
    ):
        """Test that repository errors are propagated."""
        # Arrange
        mock_stock_repository.get_historical_prices = AsyncMock(
            side_effect=RuntimeError("API error")
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="API error"):
            await use_case.execute("AMZN", datetime(2024, 1, 1), datetime(2024, 1, 31))
