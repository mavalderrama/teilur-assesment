"""Stock price entity - core business object."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class StockPrice:
    """Represents a stock price at a specific point in time."""

    symbol: str
    price: Decimal
    timestamp: datetime
    currency: str = "USD"
    volume: Optional[int] = None
    market_cap: Optional[Decimal] = None
    day_high: Optional[Decimal] = None
    day_low: Optional[Decimal] = None
    open_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty")
        if self.price < 0:
            raise ValueError("Stock price cannot be negative")
        if self.volume is not None and self.volume < 0:
            raise ValueError("Volume cannot be negative")


@dataclass(frozen=True)
class HistoricalStockPrice:
    """Represents historical stock prices over a period."""

    symbol: str
    start_date: datetime
    end_date: datetime
    prices: list[StockPrice]
    period: str  # e.g., "1d", "1wk", "1mo"

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.symbol:
            raise ValueError("Stock symbol cannot be empty")
        if self.start_date > self.end_date:
            raise ValueError("Start date must be before end date")
        if not self.prices:
            raise ValueError("Historical prices cannot be empty")

    @property
    def average_price(self) -> Decimal:
        """Calculate average price over the period."""
        if not self.prices:
            return Decimal("0")
        return sum(p.price for p in self.prices) / len(self.prices)

    @property
    def highest_price(self) -> Decimal:
        """Get highest price in the period."""
        if not self.prices:
            return Decimal("0")
        return max(p.price for p in self.prices)

    @property
    def lowest_price(self) -> Decimal:
        """Get lowest price in the period."""
        if not self.prices:
            return Decimal("0")
        return min(p.price for p in self.prices)
