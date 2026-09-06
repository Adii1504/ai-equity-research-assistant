"""
tests/test_stock_data.py
------------------------
Unit tests for the stock data fetching and parsing module.
"""

import unittest
from unittest.mock import patch
from models import StockData
from data import fetch_stock_data


class TestStockData(unittest.TestCase):

    def test_stock_data_serialisation(self):
        """StockData should serialise and deserialise correctly."""
        original = StockData(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=189.5,
            pe_ratio=28.4,
            sector="Technology",
        )
        serialised = original.to_json()
        deserialised = StockData.from_json(serialised)

        self.assertEqual(deserialised.symbol, "AAPL")
        self.assertEqual(deserialised.current_price, 189.5)
        self.assertEqual(deserialised.sector, "Technology")

    def test_stock_data_partial_fields(self):
        """StockData should handle None fields gracefully."""
        data = StockData(symbol="UNKNOWN", company_name="Unknown Corp")
        self.assertIsNone(data.current_price)
        self.assertIsNone(data.pe_ratio)
        self.assertFalse(data.from_cache)

    @patch("data.stock_data.yf.Ticker")
    def test_fetch_returns_data_on_success(self, mock_ticker_cls):
        """fetch_stock_data should return StockData with populated fields."""
        mock_info = {
            "longName": "Apple Inc.",
            "currentPrice": 189.5,
            "previousClose": 185.0,
            "marketCap": 2_900_000_000_000,
            "trailingPE": 28.4,
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "fiftyTwoWeekHigh": 199.0,
            "fiftyTwoWeekLow": 124.0,
            "volume": 50_000_000,
        }
        mock_ticker_cls.return_value.info = mock_info

        result = fetch_stock_data("AAPL")

        self.assertEqual(result.symbol, "AAPL")
        self.assertEqual(result.company_name, "Apple Inc.")
        self.assertAlmostEqual(result.current_price, 189.5)
        self.assertIsNotNone(result.price_change_pct)

    @patch("data.stock_data.yf.Ticker")
    def test_fetch_degrades_gracefully_on_failure(self, mock_ticker_cls):
        """fetch_stock_data should not raise on API failure — return partial data."""
        mock_ticker_cls.side_effect = Exception("Network error")

        result = fetch_stock_data("BADINPUT")

        self.assertEqual(result.symbol, "BADINPUT")
        self.assertIsNone(result.current_price)


if __name__ == "__main__":
    unittest.main()
