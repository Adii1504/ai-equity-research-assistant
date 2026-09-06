"""
app.py
------
Research Engine Orchestrator.

Key engineering decisions:
  1. asyncio.gather() — stock + news fetched concurrently, not sequentially.
  2. Semaphore(MAX_CONCURRENT_REQUESTS) — rate limiting.
  3. Circuit breaker — each module failure is isolated.
  4. Multi-ticker support — process N tickers concurrently.
"""

import asyncio
from typing import List, Optional

from config import MAX_CONCURRENT_REQUESTS
from data import fetch_stock_data, fetch_news
from analysis import analyse_sentiment, generate_report
from models import ResearchReport, StockData, NewsData, SentimentResult
from utils import Timer, get_logger

logger = get_logger(__name__)

# ── Rate limiter ─────────────────────────────────────────────────────────────
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def _fetch_stock_async(symbol: str) -> Optional[StockData]:
    """Wrap synchronous yfinance call for non-blocking async execution."""
    try:
        return await asyncio.to_thread(fetch_stock_data, symbol)
    except Exception as e:
        logger.error("Async stock fetch failed for %s: %s", symbol, str(e))
        return None


async def _fetch_news_async(symbol: str) -> Optional[NewsData]:
    """Wrap synchronous news fetch for non-blocking async execution."""
    try:
        return await asyncio.to_thread(fetch_news, symbol)
    except Exception as e:
        logger.error("Async news fetch failed for %s: %s", symbol, str(e))
        return None


async def _run_single(symbol: str) -> ResearchReport:
    """
    Run the full research pipeline for a single ticker.

    Pipeline:
      [stock fetch] ─┐
                     ├─ asyncio.gather() → concurrent
      [news fetch]  ─┘
                     │
                     ▼
               [sentiment analysis]
                     │
                     ▼
               [LLM report generation]
                     │
                     ▼
               [ResearchReport]
    """
    async with _semaphore:  # rate limit gate
        report = ResearchReport(symbol=symbol)

        with Timer(f"pipeline_{symbol}") as total_timer:

            # ── Stage 1: Concurrent fetch ──────────────────────────────────
            logger.info("Stage 1: concurrent stock + news fetch for %s", symbol)

            stock_data, news_data = await asyncio.gather(
                _fetch_stock_async(symbol),
                _fetch_news_async(symbol),
                return_exceptions=False,
            )

            report.stock = stock_data
            report.news = news_data

            if stock_data is None:
                report.errors.append("Stock data unavailable")
            if news_data is None:
                report.errors.append("News data unavailable")

            # ── Stage 2: Sentiment analysis ───────────────────────────────
            logger.info("Stage 2: sentiment analysis for %s", symbol)
            sentiment: Optional[SentimentResult] = None

            if news_data and news_data.articles:
                try:
                    updated_news, sentiment = await asyncio.to_thread(
                        analyse_sentiment, news_data
                    )
                    report.news = updated_news  # articles now have labels
                    report.sentiment = sentiment
                except Exception as e:
                    logger.error("Sentiment analysis failed for %s: %s", symbol, str(e))
                    report.errors.append(f"Sentiment unavailable: {str(e)}")
            else:
                logger.warning("Skipping sentiment — no articles for %s", symbol)

            # ── Stage 3: LLM report generation ────────────────────────────
            logger.info("Stage 3: LLM report generation for %s", symbol)
            try:
                summary, risks, positives, outlook, _ = await asyncio.to_thread(
                    generate_report, stock_data, news_data, sentiment
                )
                report.llm_summary = summary
                report.llm_risks = risks
                report.llm_positives = positives
                report.llm_outlook = outlook
            except Exception as e:
                logger.error("Report generation failed for %s: %s", symbol, str(e))
                report.errors.append(f"LLM report unavailable: {str(e)}")

        report.total_time_ms = total_timer.elapsed_ms
        logger.info(
            "Pipeline for %s complete in %.1f ms (errors=%d)",
            symbol, total_timer.elapsed_ms, len(report.errors)
        )

    return report


async def run_research(symbols: List[str]) -> List[ResearchReport]:
    """
    Run research pipeline for multiple tickers concurrently.

    Args:
        symbols: List of ticker strings e.g. ["AAPL", "MSFT", "TCS.NS"]

    Returns:
        List of ResearchReport, one per ticker, in original order.
    """
    symbols = [s.upper().strip() for s in symbols if s.strip()]
    if not symbols:
        return []

    logger.info("Starting concurrent research for %d ticker(s): %s", len(symbols), symbols)

    with Timer("multi_ticker_total") as t:
        reports = await asyncio.gather(
            *[_run_single(s) for s in symbols],
            return_exceptions=False,
        )

    logger.info(
        "All %d tickers complete in %.1f ms (avg %.1f ms each)",
        len(symbols), t.elapsed_ms, t.elapsed_ms / len(symbols)
    )

    return list(reports)


def research(symbols: List[str]) -> List[ResearchReport]:
    """Synchronous entry point for synchronous callers / CLI tools."""
    return asyncio.run(run_research(symbols))
