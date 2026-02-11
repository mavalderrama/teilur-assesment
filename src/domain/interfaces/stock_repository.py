"""Stock repository interface - defines contract for stock data access."""
from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.stock_price import HistoricalStockPrice, StockPrice


class IStockRepository(ABC):
    """Interface for stock data repository."""

    @abstractmethod
    async def get_realtime_price(self, symbol: str) -> StockPrice:
        """
        Get the current realtime price for a stock symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AMZN")

        Returns:
            StockPrice entity with current price data

        Raises:
            ValueError: If symbol is invalid
            RuntimeError: If price data cannot be retrieved
        """
        pass

    @abstractmethod
    async def get_historical_prices(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        period: str = "1d",
    ) -> HistoricalStockPrice:
        """
        Get historical prices for a stock symbol over a date range.

        Args:
            symbol: Stock ticker symbol (e.g., "AMZN")
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Data granularity ("1d", "1wk", "1mo")

        Returns:
            HistoricalStockPrice entity with historical data

        Raises:
            ValueError: If symbol or date range is invalid
            RuntimeError: If historical data cannot be retrieved
        """
        pass
