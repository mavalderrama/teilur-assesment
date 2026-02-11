"""Integration tests for YFinanceStockRepository."""
from datetime import datetime, timedelta

import pytest

from src.infrastructure.repositories.yfinance_stock_repository import (
    YFinanceStockRepository,
)


@pytest.mark.integration
class TestYFinanceStockRepositoryIntegration:
    """Integration tests for YFinanceStockRepository (requires internet)."""

    @pytest.fixture
    def repository(self):
        """Create repository instance."""
        return YFinanceStockRepository()

    @pytest.mark.asyncio
    async def test_get_realtime_price_for_valid_symbol(self, repository):
        """Test fetching realtime price for a valid symbol."""
        # Act
        price = await repository.get_realtime_price("AMZN")

        # Assert
        assert price.symbol == "AMZN"
        assert price.price > 0
        assert price.currency == "USD"
        assert price.timestamp is not None
        assert isinstance(price.timestamp, datetime)

    @pytest.mark.asyncio
    async def test_get_realtime_price_includes_optional_fields(self, repository):
        """Test that realtime price includes optional fields."""
        # Act
        price = await repository.get_realtime_price("AAPL")

        # Assert
        assert price.volume is None or price.volume > 0
        assert price.market_cap is None or price.market_cap > 0

    @pytest.mark.asyncio
    async def test_get_realtime_price_for_invalid_symbol_raises_error(self, repository):
        """Test that invalid symbol raises RuntimeError."""
        # Act & Assert
        with pytest.raises(RuntimeError):
            await repository.get_realtime_price("INVALID_SYMBOL_XYZ123")

    @pytest.mark.asyncio
    async def test_get_historical_prices_for_valid_inputs(self, repository):
        """Test fetching historical prices for valid inputs."""
        # Arrange
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Act
        hist = await repository.get_historical_prices("AMZN", start_date, end_date, "1d")

        # Assert
        assert hist.symbol == "AMZN"
        assert hist.start_date == start_date
        assert hist.end_date == end_date
        assert hist.period == "1d"
        assert len(hist.prices) > 0
        assert all(p.symbol == "AMZN" for p in hist.prices)
        assert hist.average_price > 0
        assert hist.highest_price >= hist.lowest_price

    @pytest.mark.asyncio
    async def test_get_historical_prices_with_weekly_period(self, repository):
        """Test fetching historical prices with weekly period."""
        # Arrange
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # Act
        hist = await repository.get_historical_prices("MSFT", start_date, end_date, "1wk")

        # Assert
        assert hist.period == "1wk"
        assert len(hist.prices) > 0

    @pytest.mark.asyncio
    async def test_get_historical_prices_for_invalid_symbol_raises_error(self, repository):
        """Test that invalid symbol raises RuntimeError."""
        # Arrange
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

        # Act & Assert
        with pytest.raises(RuntimeError):
            await repository.get_historical_prices(
                "INVALID_XYZ123", start_date, end_date, "1d"
            )

    @pytest.mark.asyncio
    async def test_get_historical_prices_with_no_data_raises_error(self, repository):
        """Test that date range with no data raises RuntimeError."""
        # Arrange - Future dates
        start_date = datetime.now() + timedelta(days=10)
        end_date = start_date + timedelta(days=7)

        # Act & Assert
        with pytest.raises(RuntimeError, match="No historical data available"):
            await repository.get_historical_prices("AMZN", start_date, end_date, "1d")
