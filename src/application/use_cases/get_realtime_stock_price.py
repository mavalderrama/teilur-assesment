"""Use case for retrieving realtime stock price."""
from src.domain.entities.stock_price import StockPrice
from src.domain.interfaces.stock_repository import IStockRepository


class GetRealtimeStockPriceUseCase:
    """Use case for getting realtime stock price."""

    def __init__(self, stock_repository: IStockRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            stock_repository: Stock repository implementation
        """
        self._stock_repository = stock_repository

    async def execute(self, symbol: str) -> StockPrice:
        """
        Execute use case to get realtime stock price.

        Args:
            symbol: Stock ticker symbol (e.g., "AMZN")

        Returns:
            StockPrice entity with current price data

        Raises:
            ValueError: If symbol is invalid or empty
            RuntimeError: If price data cannot be retrieved
        """
        # Validate input
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Stock symbol must be a non-empty string")

        # Normalize symbol to uppercase
        normalized_symbol = symbol.strip().upper()

        # Delegate to repository
        return await self._stock_repository.get_realtime_price(normalized_symbol)
