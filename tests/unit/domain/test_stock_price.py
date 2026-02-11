"""Unit tests for StockPrice entities."""
from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.entities.stock_price import HistoricalStockPrice, StockPrice


class TestStockPrice:
    """Tests for StockPrice entity."""

    def test_create_valid_stock_price(self):
        """Test creating a valid StockPrice entity."""
        price = StockPrice(
            symbol="AMZN",
            price=Decimal("185.42"),
            timestamp=datetime.now(),
            currency="USD",
            volume=1000000,
        )

        assert price.symbol == "AMZN"
        assert price.price == Decimal("185.42")
        assert price.currency == "USD"
        assert price.volume == 1000000

    def test_stock_price_immutable(self):
        """Test that StockPrice is immutable (frozen dataclass)."""
        price = StockPrice(
            symbol="AMZN",
            price=Decimal("185.42"),
            timestamp=datetime.now(),
        )

        with pytest.raises(AttributeError):
            price.symbol = "AAPL"  # type: ignore

    def test_empty_symbol_raises_error(self):
        """Test that empty symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol cannot be empty"):
            StockPrice(
                symbol="",
                price=Decimal("185.42"),
                timestamp=datetime.now(),
            )

    def test_negative_price_raises_error(self):
        """Test that negative price raises ValueError."""
        with pytest.raises(ValueError, match="Stock price cannot be negative"):
            StockPrice(
                symbol="AMZN",
                price=Decimal("-10.00"),
                timestamp=datetime.now(),
            )

    def test_negative_volume_raises_error(self):
        """Test that negative volume raises ValueError."""
        with pytest.raises(ValueError, match="Volume cannot be negative"):
            StockPrice(
                symbol="AMZN",
                price=Decimal("185.42"),
                timestamp=datetime.now(),
                volume=-1000,
            )

    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        price = StockPrice(
            symbol="AMZN",
            price=Decimal("185.42"),
            timestamp=datetime.now(),
            day_high=Decimal("190.00"),
            day_low=Decimal("180.00"),
            open_price=Decimal("182.00"),
            close_price=Decimal("185.00"),
            market_cap=Decimal("1900000000000"),
        )

        assert price.day_high == Decimal("190.00")
        assert price.day_low == Decimal("180.00")
        assert price.open_price == Decimal("182.00")
        assert price.close_price == Decimal("185.00")
        assert price.market_cap == Decimal("1900000000000")


class TestHistoricalStockPrice:
    """Tests for HistoricalStockPrice entity."""

    def test_create_valid_historical_stock_price(self):
        """Test creating a valid HistoricalStockPrice entity."""
        now = datetime.now()
        prices = [
            StockPrice(symbol="AMZN", price=Decimal("180.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("185.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("190.00"), timestamp=now),
        ]

        hist = HistoricalStockPrice(
            symbol="AMZN",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            prices=prices,
            period="1d",
        )

        assert hist.symbol == "AMZN"
        assert len(hist.prices) == 3
        assert hist.period == "1d"

    def test_empty_symbol_raises_error(self):
        """Test that empty symbol raises ValueError."""
        with pytest.raises(ValueError, match="Stock symbol cannot be empty"):
            HistoricalStockPrice(
                symbol="",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                prices=[],
                period="1d",
            )

    def test_invalid_date_range_raises_error(self):
        """Test that invalid date range raises ValueError."""
        with pytest.raises(ValueError, match="Start date must be before end date"):
            HistoricalStockPrice(
                symbol="AMZN",
                start_date=datetime(2024, 1, 31),
                end_date=datetime(2024, 1, 1),
                prices=[],
                period="1d",
            )

    def test_empty_prices_raises_error(self):
        """Test that empty prices list raises ValueError."""
        with pytest.raises(ValueError, match="Historical prices cannot be empty"):
            HistoricalStockPrice(
                symbol="AMZN",
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                prices=[],
                period="1d",
            )

    def test_average_price_calculation(self):
        """Test average price calculation."""
        now = datetime.now()
        prices = [
            StockPrice(symbol="AMZN", price=Decimal("180.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("185.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("190.00"), timestamp=now),
        ]

        hist = HistoricalStockPrice(
            symbol="AMZN",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            prices=prices,
            period="1d",
        )

        assert hist.average_price == Decimal("185.00")

    def test_highest_price_calculation(self):
        """Test highest price calculation."""
        now = datetime.now()
        prices = [
            StockPrice(symbol="AMZN", price=Decimal("180.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("185.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("190.00"), timestamp=now),
        ]

        hist = HistoricalStockPrice(
            symbol="AMZN",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            prices=prices,
            period="1d",
        )

        assert hist.highest_price == Decimal("190.00")

    def test_lowest_price_calculation(self):
        """Test lowest price calculation."""
        now = datetime.now()
        prices = [
            StockPrice(symbol="AMZN", price=Decimal("180.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("185.00"), timestamp=now),
            StockPrice(symbol="AMZN", price=Decimal("190.00"), timestamp=now),
        ]

        hist = HistoricalStockPrice(
            symbol="AMZN",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31),
            prices=prices,
            period="1d",
        )

        assert hist.lowest_price == Decimal("180.00")
