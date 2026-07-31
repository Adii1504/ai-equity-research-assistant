"""
app.py
------
Research Engine Orchestrator.

This is the most important file architecturally.

Key engineering decisions made here:
  1. asyncio.gather() — stock + news fetched concurrently, not sequentially
     Sequential: stock(1.2s) + news(0.8s) = 2.0s
     Concurrent: max(1.2s, 0.8s) = 1.2s   → ~40% latency reduction

  2. Semaphore(MAX_CONCURRENT_REQUESTS) — rate limiting
     Prevents overwhelming external APIs under high load
     GS systems handle thousands of requests — this is production thinking

  3. Circuit breaker — each module failure is isolated
     If news fails, stock + sentiment still run
     Partial report > no report

  4. Multi-ticker support — process N tickers concurrently
     3 tickers sequential = 3 × single_ticker_time
     3 tickers concurrent = ~1 × single_ticker_time

This is the asyncio.gather() usage that interviewers ask about.
Be ready to explain: "What happens without gather()? Why does concurrent matter here?"
"""

import asyncio
import time
from typing import List, Optional

from data.stock_data import fetch_stock_data
from data.news_data import fetch_news
from analysis.sentiment import analyse_sentiment
from analysis.report_generator import generate_report
from models.stock_model import ResearchReport, StockData, NewsData, SentimentResult
from utils.timer import Timer
from utils.logger import get_logger
from config import MAX_CONCURRENT_REQUESTS

logger = get_logger(__name__)

# ── Rate limiter ─────────────────────────────────────────────────────────────
# Limits concurrent requests across all tickers.
# ADR: Why Semaphore vs a queue?
#   Semaphore is simpler for a max-concurrency constraint.
#   A queue (e.g. asyncio.Queue) would be better for prioritisation — future enhancement.
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)


async def _fetch_stock_async(symbol: str) -> Optional[StockData]:
    """Wrap synchronous yfinance call for async execution."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, fetch_stock_data, symbol)
    except Exception as e:
        logger.error("Async stock fetch failed for %s: %s", symbol, str(e))
        return None


async def _fetch_news_async(symbol: str) -> Optional[NewsData]:
    """Wrap synchronous news fetch for async execution."""
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(None, fetch_news, symbol)
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
    async with _semaphore:                         # rate limit gate
        report = ResearchReport(symbol=symbol)

        with Timer(f"pipeline_{symbol}") as total_timer:

            # ── Stage 1: Concurrent fetch ──────────────────────────────────
            logger.info("Stage 1: concurrent stock + news fetch for %s", symbol)

            stock_data, news_data = await asyncio.gather(
                _fetch_stock_async(symbol),
                _fetch_news_async(symbol),
                return_exceptions=False,           # we handle errors inside each fetch
            )

            report.stock = stock_data
            report.news  = news_data

            if stock_data is None:
                report.errors.append("Stock data unavailable")
            if news_data is None:
                report.errors.append("News data unavailable")

            # ── Stage 2: Sentiment analysis ───────────────────────────────
            logger.info("Stage 2: sentiment analysis for %s", symbol)
            sentiment: Optional[SentimentResult] = None

            if news_data and news_data.articles:
                try:
                    loop = asyncio.get_event_loop()
                    updated_news, sentiment = await loop.run_in_executor(
                        None, analyse_sentiment, news_data
                    )
                    report.news      = updated_news    # articles now have labels
                    report.sentiment = sentiment
                except Exception as e:
                    logger.error("Sentiment analysis failed: %s", str(e))
                    report.errors.append(f"Sentiment unavailable: {str(e)}")
            else:
                logger.warning("Skipping sentiment — no articles for %s", symbol)

            # ── Stage 3: LLM report generation ────────────────────────────
            logger.info("Stage 3: LLM report generation for %s", symbol)
            try:
                loop = asyncio.get_event_loop()
                summary, risks, positives, outlook, llm_ms = await loop.run_in_executor(
                    None, generate_report, stock_data, news_data, sentiment
                )
                report.llm_summary   = summary
                report.llm_risks     = risks
                report.llm_positives = positives
                report.llm_outlook   = outlook
            except Exception as e:
                logger.error("Report generation failed: %s", str(e))
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

    This is the multi-ticker demonstration:
      3 tickers sequential = ~9s total
      3 tickers concurrent = ~3s total  (bounded by slowest single ticker)

    Args:
        symbols: List of ticker strings e.g. ["AAPL", "MSFT", "TCS.NS"]

    Returns:
        List of ResearchReport, one per ticker, in the same order.
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
    """
    Synchronous entry point for Streamlit (which can't use async directly).

    Streamlit runs in a synchronous context — we create a new event loop
    and run the async pipeline inside it.
    """
    return asyncio.run(run_research(symbols))
