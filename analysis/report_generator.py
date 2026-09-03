

import json
import re
from typing import Optional

from groq import Groq

from models.stock_model import StockData, NewsData, SentimentResult, ResearchReport
from utils.timer import Timer
from utils.logger import get_logger
from config import GROQ_API_KEY, GROQ_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE

logger = get_logger(__name__)


def _format_market_cap(val: Optional[float]) -> str:
    if val is None:
        return "N/A"
    if val >= 1e12:
        return f"${val/1e12:.2f}T"
    if val >= 1e9:
        return f"${val/1e9:.2f}B"
    if val >= 1e6:
        return f"${val/1e6:.2f}M"
    return f"${val:,.0f}"


def _build_prompt(
    stock: Optional[StockData],
    news: Optional[NewsData],
    sentiment: Optional[SentimentResult],
) -> str:
    """
    Build a structured, data-grounded prompt.
    Grounding the LLM in specific numbers reduces hallucination significantly.
    """
    lines = ["You are a professional equity research analyst. Using ONLY the data provided below, generate a concise research note."]
    lines.append("Respond ONLY in this exact JSON format:\n")
    lines.append('{"summary": "...", "risks": "...", "positives": "...", "outlook": "..."}')
    lines.append("\nEach section should be 2-3 sentences. Be specific — reference the actual numbers provided.\n")
    lines.append("--- DATA ---")

    if stock:
        lines.append(f"\nCOMPANY: {stock.company_name} ({stock.symbol})")
        lines.append(f"SECTOR: {stock.sector or 'N/A'} | INDUSTRY: {stock.industry or 'N/A'}")
        lines.append(f"CURRENT PRICE: ${stock.current_price or 'N/A'}")
        lines.append(f"PRICE CHANGE: {stock.price_change_pct or 'N/A'}% today")
        lines.append(f"MARKET CAP: {_format_market_cap(stock.market_cap)}")
        lines.append(f"P/E RATIO: {stock.pe_ratio or 'N/A'}")
        lines.append(f"52-WEEK HIGH: ${stock.week_52_high or 'N/A'} | LOW: ${stock.week_52_low or 'N/A'}")

    if sentiment:
        lines.append(f"\nNEWS SENTIMENT: {sentiment.overall_label.upper()} (confidence: {sentiment.overall_score:.2f})")
        lines.append(f"POSITIVE articles: {sentiment.positive_count} | NEUTRAL: {sentiment.neutral_count} | NEGATIVE: {sentiment.negative_count}")

    if news and news.articles:
        lines.append("\nTOP HEADLINES:")
        for i, article in enumerate(news.articles[:5], 1):
            label = article.sentiment_label or "neutral"
            lines.append(f"  {i}. [{label.upper()}] {article.title} — {article.publisher}")

    lines.append("\n--- END DATA ---")
    lines.append("\nGenerate the JSON research note now:")

    return "\n".join(lines)


def _parse_llm_response(text: str) -> dict:
    """
    Extract JSON from LLM response even if there's surrounding text.
    LLMs sometimes wrap JSON in markdown code blocks — handle that.
    """
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Extract first {...} block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Return raw text as summary if all parsing fails
    logger.warning("Could not parse LLM JSON response — using raw text as summary")
    return {
        "summary":   text[:500],
        "risks":     "Analysis unavailable",
        "positives": "Analysis unavailable",
        "outlook":   "Analysis unavailable",
    }


def generate_report(
    stock: Optional[StockData],
    news: Optional[NewsData],
    sentiment: Optional[SentimentResult],
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], float]:
    """
    Call Groq LLM with structured prompt and return parsed sections.

    Returns:
        Tuple of (summary, risks, positives, outlook, elapsed_ms)
        Any section can be None if generation fails.
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set in .env — skipping LLM report generation")
        return (
            "LLM report unavailable — add GROQ_API_KEY to .env",
            None, None, None, 0.0
        )

    prompt = _build_prompt(stock, news, sentiment)
    logger.info("Calling Groq LLM (%s) for report generation", GROQ_MODEL)

    with Timer("llm_report_generation") as t:
        try:
            client   = Groq(api_key=GROQ_API_KEY)
            response = client.chat.completions.create(
                model       = GROQ_MODEL,
                messages    = [{"role": "user", "content": prompt}],
                max_tokens  = LLM_MAX_TOKENS,
                temperature = LLM_TEMPERATURE,
            )
            raw_text = response.choices[0].message.content
            parsed   = _parse_llm_response(raw_text)

            logger.info("LLM report generated in %.1f ms", t.elapsed_ms)

            return (
                parsed.get("summary"),
                parsed.get("risks"),
                parsed.get("positives"),
                parsed.get("outlook"),
                t.elapsed_ms,
            )

        except Exception as e:
            logger.error("LLM report generation failed: %s", str(e))
            return (
                f"Report generation failed: {str(e)}",
                None, None, None, t.elapsed_ms
            )
