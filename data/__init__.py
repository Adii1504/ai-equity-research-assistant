"""
data
----
Data ingestion, catalogs, and synthetic providers.
"""

from data.stock_data import fetch_stock_data
from data.news_data import fetch_news
from data.stocks_catalog import get_stock_catalog, get_sector_for_symbol
from data.funds_data import get_mock_funds
from data.synthetic_data import get_synthetic_market_data

__all__ = [
    "fetch_stock_data",
    "fetch_news",
    "get_stock_catalog",
    "get_sector_for_symbol",
    "get_mock_funds",
    "get_synthetic_market_data",
]
