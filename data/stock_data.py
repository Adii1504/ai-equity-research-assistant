"""
data/stock_data.py
------------------
Fetches stock fundamentals from Yahoo Finance via yfinance.

Responsibilities:
  - Connect to Yahoo Finance
  - Retrieve and validate stock metrics
  - Return typed StockData object
  - Cache results to avoid redundant API calls

Input:  ticker symbol (str)
Output: StockData dataclass
"""

import yfinance as yf
from typing import Optional

from models.stock_model import StockData
from utils.cache import cache
from utils.timer import Timer
from utils.logger import get_logger
from config import CACHE_TTL_STOCK

logger = get_logger(__name__)

CACHE_PREFIX = "stock:"


def _safe_float(val) -> Optional[float]:
    """Convert yfinance values (which can be None, str, or numeric) to float."""
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _safe_int(val) -> Optional[int]:
    try:
        return int(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def fetch_stock_data(symbol: str) -> StockData:
    """
    Fetch stock fundamentals for the given ticker.
    Checks Redis cache first — only calls yfinance on a cache miss.

    Args:
        symbol: Ticker symbol e.g. "AAPL", "TCS.NS", "RELIANCE.NS"

    Returns:
        StockData with available fields populated.
        Never raises — returns partial data on failure.
    """
    symbol = symbol.upper().strip()
    cache_key = f"{CACHE_PREFIX}{symbol}"

    # ── Cache check ────────────────────────────────────────────────────────
    cached = cache.get(cache_key)
    if cached:
        try:
            data = StockData.from_json(cached)
            data.from_cache = True
            remaining = cache.ttl(cache_key)
            logger.info(
                "Cache HIT for %s — %d seconds remaining", symbol, remaining
            )
            return data
        except Exception as e:
            logger.warning("Failed to deserialise cached stock data: %s", str(e))

    # ── Live fetch ─────────────────────────────────────────────────────────
    logger.info("Fetching live stock data for %s", symbol)

    with Timer(f"stock_fetch_{symbol}") as t:
        try:
            ticker = yf.Ticker(symbol)
            info   = ticker.info

            # price change calculation
            current  = _safe_float(info.get("currentPrice") or info.get("regularMarketPrice"))
            previous = _safe_float(info.get("previousClose") or info.get("regularMarketPreviousClose"))
            change     = round(current - previous, 4) if current and previous else None
            change_pct = round((change / previous) * 100, 2) if change and previous else None

            data = StockData(
                symbol           = symbol,
                company_name     = info.get("longName") or info.get("shortName") or symbol,
                current_price    = current,
                previous_close   = previous,
                price_change     = change,
                price_change_pct = change_pct,
                market_cap       = _safe_float(info.get("marketCap")),
                pe_ratio         = _safe_float(info.get("trailingPE") or info.get("forwardPE")),
                volume           = _safe_int(info.get("volume") or info.get("regularMarketVolume")),
                week_52_high     = _safe_float(info.get("fiftyTwoWeekHigh")),
                week_52_low      = _safe_float(info.get("fiftyTwoWeekLow")),
                sector           = info.get("sector"),
                industry         = info.get("industry"),
                from_cache       = False,
            )

        except Exception as e:
            logger.error("Failed to fetch stock data for %s: %s", symbol, str(e))
            # Graceful degradation — return minimal object rather than crashing
            data = StockData(
                symbol       = symbol,
                company_name = symbol,
                from_cache   = False,
            )

    data.fetch_time_ms = t.elapsed_ms
    logger.info(
        "Stock data for %s fetched in %.1f ms (price=%.2f)",
        symbol,
        t.elapsed_ms,
        data.current_price or 0,
    )

    # ── Cache write ────────────────────────────────────────────────────────
    try:
        cache.set(cache_key, data.to_json(), ttl=CACHE_TTL_STOCK)
    except Exception as e:
        logger.warning("Failed to cache stock data: %s", str(e))

    return data
