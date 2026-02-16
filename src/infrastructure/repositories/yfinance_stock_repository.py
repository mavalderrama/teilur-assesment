"""YFinance stock repository implementation."""
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any

import yfinance as yf

from src.domain.entities.stock_price import HistoricalStockPrice, StockPrice
from src.domain.interfaces.stock_repository import IStockRepository
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class YFinanceStockRepository(IStockRepository):
    """Repository implementation using yfinance library."""

    def __init__(self) -> None:
        """Initialize repository."""
        logger.info("YFinance stock repository initialized")

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
        logger.info("Fetching realtime stock price", extra={"symbol": symbol})

        try:
            # Run blocking yfinance call in thread pool
            ticker = await asyncio.to_thread(yf.Ticker, symbol)
            info = await asyncio.to_thread(lambda: ticker.info)

            # Validate data was retrieved
            if not info or "currentPrice" not in info:
                logger.error("No price data available", extra={"symbol": symbol})
                raise RuntimeError(f"Could not retrieve price data for symbol: {symbol}")

            # Extract price data
            current_price = info.get("currentPrice") or info.get("regularMarketPrice")
            if current_price is None:
                logger.error("Price field not found", extra={"symbol": symbol})
                raise RuntimeError(f"No price available for symbol: {symbol}")

            logger.info(
                "Realtime price fetched successfully",
                extra={"symbol": symbol, "price": float(current_price)},
            )

            return StockPrice(
                symbol=symbol,
                price=Decimal(str(current_price)),
                timestamp=datetime.now(),
                currency=info.get("currency", "USD"),
                volume=info.get("volume"),
                market_cap=Decimal(str(info["marketCap"])) if info.get("marketCap") else None,
                day_high=Decimal(str(info["dayHigh"])) if info.get("dayHigh") else None,
                day_low=Decimal(str(info["dayLow"])) if info.get("dayLow") else None,
                open_price=Decimal(str(info["open"])) if info.get("open") else None,
                close_price=(
                    Decimal(str(info["previousClose"])) if info.get("previousClose") else None
                ),
            )

        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            logger.error(
                "Failed to fetch realtime price",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(f"Failed to retrieve realtime price for {symbol}: {str(e)}")

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
        logger.info(
            "Fetching historical stock prices",
            extra={
                "symbol": symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period": period,
            },
        )

        try:
            # Run blocking yfinance call in thread pool
            ticker = await asyncio.to_thread(yf.Ticker, symbol)

            # Download historical data
            hist = await asyncio.to_thread(
                lambda: ticker.history(
                    start=start_date.strftime("%Y-%m-%d"),
                    end=end_date.strftime("%Y-%m-%d"),
                    interval=period,
                )
            )

            if hist.empty:
                logger.error(
                    "No historical data available",
                    extra={"symbol": symbol, "start_date": start_date, "end_date": end_date},
                )
                raise RuntimeError(
                    f"No historical data available for {symbol} "
                    f"between {start_date} and {end_date}"
                )

            # Convert DataFrame to list of StockPrice entities
            prices = []
            for index, row in hist.iterrows():
                prices.append(
                    StockPrice(
                        symbol=symbol,
                        price=Decimal(str(row["Close"])),
                        timestamp=index.to_pydatetime(),
                        currency="USD",
                        volume=int(row["Volume"]) if "Volume" in row else None,
                        day_high=Decimal(str(row["High"])) if "High" in row else None,
                        day_low=Decimal(str(row["Low"])) if "Low" in row else None,
                        open_price=Decimal(str(row["Open"])) if "Open" in row else None,
                        close_price=Decimal(str(row["Close"])),
                    )
                )

            logger.info(
                "Historical prices fetched successfully",
                extra={"symbol": symbol, "data_points": len(prices)},
            )

            return HistoricalStockPrice(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                prices=prices,
                period=period,
            )

        except Exception as e:
            if isinstance(e, (ValueError, RuntimeError)):
                raise
            logger.error(
                "Failed to fetch historical prices",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True,
            )
            raise RuntimeError(
                f"Failed to retrieve historical prices for {symbol}: {str(e)}"
            )
