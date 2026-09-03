"""
data/stocks_catalog.py
------------------------
A small curated universe of tickers with sector tags.

This is NOT live data — it's just the list of symbols we know about,
so the /stocks page and the recommendation engine have something to
work with. Live prices/fundamentals for any of these still come from
data/stock_data.py (yfinance) when the user clicks through to analyse one.
"""

from typing import List, Dict

_CATALOG: List[Dict] = [
    {"symbol": "AAPL",  "name": "Apple Inc.",            "sector": "Technology"},
    {"symbol": "MSFT",  "name": "Microsoft Corp.",       "sector": "Technology"},
    {"symbol": "GOOGL", "name": "Alphabet Inc.",         "sector": "Technology"},
    {"symbol": "NVDA",  "name": "NVIDIA Corp.",          "sector": "Technology"},
    {"symbol": "META",  "name": "Meta Platforms Inc.",   "sector": "Technology"},
    {"symbol": "AMZN",  "name": "Amazon.com Inc.",       "sector": "Consumer Discretionary"},
    {"symbol": "TSLA",  "name": "Tesla Inc.",            "sector": "Consumer Discretionary"},
    {"symbol": "NFLX",  "name": "Netflix Inc.",          "sector": "Communication Services"},
    {"symbol": "JPM",   "name": "JPMorgan Chase & Co.",  "sector": "Financials"},
    {"symbol": "V",     "name": "Visa Inc.",             "sector": "Financials"},
    {"symbol": "TCS.NS",       "name": "Tata Consultancy Services", "sector": "Technology"},
    {"symbol": "RELIANCE.NS",  "name": "Reliance Industries",       "sector": "Energy"},
    {"symbol": "INFY.NS",      "name": "Infosys Ltd.",              "sector": "Technology"},
    {"symbol": "HDFCBANK.NS",  "name": "HDFC Bank Ltd.",            "sector": "Financials"},
]


def get_stock_catalog() -> List[Dict]:
    return _CATALOG


def get_sector_for_symbol(symbol: str) -> str:
    for item in _CATALOG:
        if item["symbol"].upper() == symbol.upper():
            return item["sector"]
    return "Unknown"