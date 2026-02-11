"""LangGraph tools for the AI agent."""
from datetime import datetime, timedelta
from typing import Any

from langchain_core.tools import tool

from src.application.use_cases.get_historical_stock_price import (
    GetHistoricalStockPriceUseCase,
)
from src.application.use_cases.get_realtime_stock_price import (
    GetRealtimeStockPriceUseCase,
)
from src.application.use_cases.query_documents import QueryDocumentsUseCase


class AgentTools:
    """Factory for creating agent tools with dependency injection."""

    def __init__(
        self,
        get_realtime_price_uc: GetRealtimeStockPriceUseCase,
        get_historical_price_uc: GetHistoricalStockPriceUseCase,
        query_documents_uc: QueryDocumentsUseCase,
    ) -> None:
        """
        Initialize agent tools with use cases.

        Args:
            get_realtime_price_uc: Use case for getting realtime stock price
            get_historical_price_uc: Use case for getting historical prices
            query_documents_uc: Use case for querying documents
        """
        self._get_realtime_price_uc = get_realtime_price_uc
        self._get_historical_price_uc = get_historical_price_uc
        self._query_documents_uc = query_documents_uc

    def create_tools(self) -> list[Any]:
        """
        Create all tools for the agent.

        Returns:
            List of LangChain tools
        """

        @tool
        async def get_realtime_stock_price(symbol: str) -> str:
            """
            Get the current realtime stock price for a given ticker symbol.

            Args:
                symbol: Stock ticker symbol (e.g., 'AMZN', 'AAPL')

            Returns:
                Current stock price and related information
            """
            try:
                price = await self._get_realtime_price_uc.execute(symbol)
                return (
                    f"Stock: {price.symbol}\n"
                    f"Current Price: ${price.price:.2f} {price.currency}\n"
                    f"Timestamp: {price.timestamp.isoformat()}\n"
                    f"Day High: ${price.day_high:.2f if price.day_high else 'N/A'}\n"
                    f"Day Low: ${price.day_low:.2f if price.day_low else 'N/A'}\n"
                    f"Open: ${price.open_price:.2f if price.open_price else 'N/A'}\n"
                    f"Volume: {price.volume:,} if price.volume else 'N/A'}\n"
                    f"Market Cap: ${price.market_cap:,.0f if price.market_cap else 'N/A'}"
                )
            except Exception as e:
                return f"Error retrieving stock price for {symbol}: {str(e)}"

        @tool
        async def get_historical_stock_prices(
            symbol: str, start_date: str, end_date: str, period: str = "1d"
        ) -> str:
            """
            Get historical stock prices for a given ticker symbol over a date range.

            Args:
                symbol: Stock ticker symbol (e.g., 'AMZN', 'AAPL')
                start_date: Start date in YYYY-MM-DD format
                end_date: End date in YYYY-MM-DD format
                period: Data granularity - '1d' for daily, '1wk' for weekly, '1mo' for monthly

            Returns:
                Historical stock prices and statistics
            """
            try:
                # Parse dates
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y-%m-%d")

                # Get historical data
                hist_prices = await self._get_historical_price_uc.execute(
                    symbol, start, end, period
                )

                # Format response
                result = (
                    f"Historical Stock Prices for {hist_prices.symbol}\n"
                    f"Period: {hist_prices.start_date.date()} to {hist_prices.end_date.date()}\n"
                    f"Granularity: {hist_prices.period}\n"
                    f"Number of data points: {len(hist_prices.prices)}\n\n"
                    f"Statistics:\n"
                    f"- Average Price: ${hist_prices.average_price:.2f}\n"
                    f"- Highest Price: ${hist_prices.highest_price:.2f}\n"
                    f"- Lowest Price: ${hist_prices.lowest_price:.2f}\n\n"
                    f"Recent prices:\n"
                )

                # Add last 5 prices
                for price in hist_prices.prices[-5:]:
                    result += (
                        f"  {price.timestamp.date()}: ${price.price:.2f}\n"
                    )

                return result

            except Exception as e:
                return (
                    f"Error retrieving historical prices for {symbol}: {str(e)}"
                )

        @tool
        async def search_financial_documents(query: str, max_results: int = 5) -> str:
            """
            Search Amazon's financial documents (annual reports, earnings releases) for relevant information.

            Args:
                query: Search query describing what information to find
                max_results: Maximum number of document chunks to return (default: 5)

            Returns:
                Relevant excerpts from financial documents
            """
            try:
                chunks = await self._query_documents_uc.execute(query, max_results)

                if not chunks:
                    return "No relevant information found in financial documents."

                result = f"Found {len(chunks)} relevant document sections:\n\n"

                for idx, chunk in enumerate(chunks, 1):
                    result += (
                        f"[{idx}] (Relevance: {chunk.relevance_score:.2f})\n"
                        f"{chunk.content}\n\n"
                    )

                return result

            except Exception as e:
                return f"Error searching financial documents: {str(e)}"

        return [
            get_realtime_stock_price,
            get_historical_stock_prices,
            search_financial_documents,
        ]
