"""
data/news_data.py
-----------------
Fetches recent news articles for a given ticker.

Primary source:   yfinance built-in news feed (no API key needed)
Fallback source:  NewsAPI.org (requires free API key)

Circuit breaker pattern:
  If primary source fails → try fallback
  If both fail → return NewsData with error flag (graceful degradation)
  The rest of the pipeline continues without news — partial report is better than no report.

Input:  ticker symbol (str)
Output: NewsData dataclass containing list of NewsArticle
"""

import requests
from datetime import datetime, timedelta
from typing import List, Optional
import yfinance as yf

from models.stock_model import NewsData, NewsArticle
from utils.cache import cache
from utils.timer import Timer
from utils.logger import get_logger
from config import CACHE_TTL_NEWS, NEWS_API_KEY, MAX_NEWS_ARTICLES, NEWS_LOOKBACK_DAYS

logger = get_logger(__name__)

CACHE_PREFIX = "news:"


def _parse_yfinance_articles(raw_articles: list, limit: int) -> List[NewsArticle]:
    """Convert raw yfinance news dicts into typed NewsArticle objects."""
    articles = []
    for item in raw_articles[:limit]:
        try:
            # yfinance returns providerPublishTime as Unix timestamp
            ts = item.get("providerPublishTime", 0)
            published = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M UTC") if ts else "Unknown"

            articles.append(NewsArticle(
                title       = item.get("title", "No title"),
                publisher   = item.get("publisher", "Unknown"),
                published_at= published,
                url         = item.get("link", ""),
                description = None,     # yfinance doesn't provide description
            ))
        except Exception as e:
            logger.warning("Failed to parse article: %s", str(e))
            continue
    return articles


def _fetch_from_newsapi(symbol: str, limit: int) -> List[NewsArticle]:
    """
    Fallback: fetch from NewsAPI.org free tier.
    Returns empty list if API key is not set or request fails.
    """
    if not NEWS_API_KEY:
        logger.debug("NewsAPI key not set — skipping fallback")
        return []

    try:
        from_date = (datetime.utcnow() - timedelta(days=NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q":        symbol,
            "from":     from_date,
            "sortBy":   "publishedAt",
            "pageSize": limit,
            "apiKey":   NEWS_API_KEY,
            "language": "en",
        }
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        data = resp.json()

        articles = []
        for item in data.get("articles", []):
            articles.append(NewsArticle(
                title       = item.get("title", "No title"),
                publisher   = item.get("source", {}).get("name", "Unknown"),
                published_at= item.get("publishedAt", "Unknown"),
                url         = item.get("url", ""),
                description = item.get("description"),
            ))
        logger.info("NewsAPI fallback returned %d articles", len(articles))
        return articles

    except Exception as e:
        logger.error("NewsAPI fallback failed: %s", str(e))
        return []


def fetch_news(symbol: str) -> NewsData:
    """
    Fetch recent news for a ticker symbol.
    Primary: yfinance news | Fallback: NewsAPI | Graceful degradation on failure.

    Args:
        symbol: Ticker e.g. "AAPL", "TCS.NS"

    Returns:
        NewsData — articles list may be empty if all sources fail,
        but error field will explain why. Never raises.
    """
    symbol    = symbol.upper().strip()
    cache_key = f"{CACHE_PREFIX}{symbol}"

    # ── Cache check ────────────────────────────────────────────────────────
    cached = cache.get(cache_key)
    if cached:
        try:
            data = NewsData.from_json(cached)
            data.from_cache = True
            logger.info("Cache HIT for news:%s", symbol)
            return data
        except Exception as e:
            logger.warning("Failed to deserialise cached news: %s", str(e))

    # ── Primary: yfinance news feed ────────────────────────────────────────
    logger.info("Fetching live news for %s", symbol)

    with Timer(f"news_fetch_{symbol}") as t:
        articles: List[NewsArticle] = []
        error: Optional[str] = None

        try:
            ticker      = yf.Ticker(symbol)
            raw         = ticker.news or []
            articles    = _parse_yfinance_articles(raw, MAX_NEWS_ARTICLES)
            logger.info("yfinance returned %d articles for %s", len(articles), symbol)

        except Exception as e:
            logger.warning(
                "yfinance news fetch failed for %s: %s — trying NewsAPI fallback",
                symbol, str(e)
            )
            # ── Fallback: NewsAPI ──────────────────────────────────────────
            articles = _fetch_from_newsapi(symbol, MAX_NEWS_ARTICLES)

            if not articles:
                error = f"News unavailable: {str(e)}"
                logger.error("All news sources failed for %s", symbol)

    data = NewsData(
        symbol        = symbol,
        articles      = articles,
        fetch_time_ms = t.elapsed_ms,
        from_cache    = False,
        error         = error,
    )

    logger.info(
        "News for %s: %d articles in %.1f ms (error=%s)",
        symbol, len(articles), t.elapsed_ms, error
    )

    # ── Cache write ────────────────────────────────────────────────────────
    try:
        cache.set(cache_key, data.to_json(), ttl=CACHE_TTL_NEWS)
    except Exception as e:
        logger.warning("Failed to cache news data: %s", str(e))

    return data
