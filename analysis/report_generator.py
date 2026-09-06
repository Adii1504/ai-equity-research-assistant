"""
analysis/report_generator.py
----------------------------
Structured LLM equity research note generator using Groq API.
"""

import json
import re
from typing import Optional, Tuple
from groq import Groq

from config import GROQ_API_KEY, GROQ_MODEL, LLM_MAX_TOKENS, LLM_TEMPERATURE
from models import StockData, NewsData, SentimentResult
from utils import Timer, get_logger

logger = get_logger(__name__)


def _format_market_cap(val: Optional[float]) -> str:
    """Format market cap numbers into human-readable strings."""
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
    lines = [
        "You are a professional equity research analyst. Using ONLY the data provided below, generate a concise research note.",
        "Respond ONLY in this exact JSON format:\n",
        '{"summary": "...", "risks": "...", "positives": "...", "outlook": "..."}',
        "\nEach section should be 2-3 sentences. Be specific — reference the actual numbers provided.\n",
        "--- DATA ---",
    ]

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
        lines.append(
            f"POSITIVE articles: {sentiment.positive_count} | NEUTRAL: {sentiment.neutral_count} | NEGATIVE: {sentiment.negative_count}"
        )

    if news and news.articles:
        lines.append("\nTOP HEADLINES:")
        for i, article in enumerate(news.articles[:5], 1):
            label = article.sentiment_label or "neutral"
            lines.append(f"  {i}. [{label.upper()}] {article.title} — {article.publisher}")

    lines.append("\n--- END DATA ---")
    lines.append("\nGenerate the JSON research note now:")

    return "\n".join(lines)


def _parse_llm_response(text: str) -> dict:
    """Extract JSON from LLM response even if wrapped in markdown code blocks."""
    text = re.sub(r"```(?:json)?", "", text).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse LLM JSON response — using raw text as summary")
    return {
        "summary": text[:500],
        "risks": "Analysis unavailable",
        "positives": "Analysis unavailable",
        "outlook": "Analysis unavailable",
    }


def generate_report(
    stock: Optional[StockData],
    news: Optional[NewsData],
    sentiment: Optional[SentimentResult],
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], float]:
    """
    Call Groq LLM with structured prompt and return parsed sections.

    Returns:
        Tuple of (summary, risks, positives, outlook, elapsed_ms)
    """
    if not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set in .env — skipping LLM report generation")
        return (
            "LLM report unavailable — add GROQ_API_KEY to .env",
            None,
            None,
            None,
            0.0,
        )

    prompt = _build_prompt(stock, news, sentiment)

    candidate_models = [
        GROQ_MODEL,
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "groq/compound-mini",
        "openai/gpt-oss-20b",
        "qwen/qwen3.6-27b",
    ]
    models_to_try = list(dict.fromkeys([m for m in candidate_models if m]))

    parsed_report = None
    with Timer("llm_report_generation") as t:
        client = Groq(api_key=GROQ_API_KEY)
        last_error = None

        for model_name in models_to_try:
            try:
                logger.info("Calling Groq LLM (%s) for report generation", model_name)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=LLM_MAX_TOKENS,
                    temperature=LLM_TEMPERATURE,
                )
                raw_text = response.choices[0].message.content or ""
                parsed_report = _parse_llm_response(raw_text)

                logger.info("LLM report generated with %s", model_name)
                break

            except Exception as e:
                last_error = e
                logger.warning("Groq model %s failed: %s — trying next candidate", model_name, str(e))
                continue

    if parsed_report:
        return (
            parsed_report.get("summary"),
            parsed_report.get("risks"),
            parsed_report.get("positives"),
            parsed_report.get("outlook"),
            t.elapsed_ms,
        )

    logger.error("All LLM candidate models failed. Last error: %s", str(last_error))
    return (
        f"Report generation failed: {str(last_error)}",
        None,
        None,
        None,
        t.elapsed_ms,
    )
