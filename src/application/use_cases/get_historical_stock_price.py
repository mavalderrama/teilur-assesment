"""Use case for retrieving historical stock prices."""
from datetime import datetime

from src.domain.entities.stock_price import HistoricalStockPrice
from src.domain.interfaces.stock_repository import IStockRepository


class GetHistoricalStockPriceUseCase:
    """Use case for getting historical stock prices."""

    def __init__(self, stock_repository: IStockRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            stock_repository: Stock repository implementation
        """
        self._stock_repository = stock_repository

    async def execute(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        period: str = "1d",
    ) -> HistoricalStockPrice:
        """
        Execute use case to get historical stock prices.

        Args:
            symbol: Stock ticker symbol (e.g., "AMZN")
            start_date: Start date for historical data
            end_date: End date for historical data
            period: Data granularity ("1d", "1wk", "1mo")

        Returns:
            HistoricalStockPrice entity with historical data

        Raises:
            ValueError: If inputs are invalid
            RuntimeError: If historical data cannot be retrieved
        """
        # Validate inputs
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Stock symbol must be a non-empty string")

        if not isinstance(start_date, datetime):
            raise ValueError("Start date must be a datetime object")

        if not isinstance(end_date, datetime):
            raise ValueError("End date must be a datetime object")

        if start_date >= end_date:
            raise ValueError("Start date must be before end date")

        if period not in ["1d", "1wk", "1mo"]:
            raise ValueError("Period must be one of: 1d, 1wk, 1mo")

        # Normalize symbol to uppercase
        normalized_symbol = symbol.strip().upper()

        # Delegate to repository
        return await self._stock_repository.get_historical_prices(
            normalized_symbol, start_date, end_date, period
        )
