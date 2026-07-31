"""
analysis/sentiment.py
---------------------
Sentiment analysis using ProsusAI/finbert.

ADR: Why FinBERT over VADER or TextBlob?
  - FinBERT is trained specifically on financial communications (earnings calls,
    analyst reports, financial news) — general models misread finance language.
  - Example: "Apple beats earnings" → VADER: neutral | FinBERT: positive (0.97)
  - Example: "Margin compression" → VADER: neutral | FinBERT: negative (0.89)
  - This domain specificity is the technical differentiator worth mentioning in interviews.

ADR: Why run locally rather than API?
  - Zero cost, no rate limits, no latency from external HTTP
  - Model loads once, then inference is ~50ms per headline
  - Keeps sensitive financial queries off third-party servers

Input:  NewsData (with articles list)
Output: SentimentResult + mutated articles (each gets label + score)
"""

from typing import Optional, List
from models.stock_model import NewsData, SentimentResult, NewsArticle
from utils.timer import Timer
from utils.logger import get_logger

logger = get_logger(__name__)

# ── Lazy model loading ────────────────────────────────────────────────────────
# Load once on first call — subsequent calls reuse the same model in memory.
# This avoids 3s startup cost on every request.
_pipeline = None


def _get_pipeline():
    global _pipeline
    if _pipeline is None:
        logger.info("Loading FinBERT model (first run only)…")
        try:
            from transformers import pipeline as hf_pipeline
            from config import FINBERT_MODEL
            _pipeline = hf_pipeline(
                "text-classification",
                model=FINBERT_MODEL,
                tokenizer=FINBERT_MODEL,
                truncation=True,
                max_length=512,
            )
            logger.info("FinBERT loaded successfully")
        except Exception as e:
            logger.error("Failed to load FinBERT: %s — falling back to rule-based", str(e))
            _pipeline = "fallback"
    return _pipeline


def _rule_based_sentiment(text: str) -> tuple[str, float]:
    """
    Lightweight fallback when FinBERT is unavailable.
    Keyword-based — not accurate but keeps the pipeline alive.
    """
    text_lower = text.lower()
    positive_words = {
        "beat", "record", "profit", "growth", "rise", "gain", "surge",
        "up", "high", "strong", "positive", "bullish", "upgrade", "outperform"
    }
    negative_words = {
        "loss", "miss", "decline", "fall", "drop", "down", "weak",
        "negative", "bearish", "downgrade", "underperform", "cut", "layoff"
    }
    pos = sum(1 for w in positive_words if w in text_lower)
    neg = sum(1 for w in negative_words if w in text_lower)

    if pos > neg:
        return "positive", 0.6
    elif neg > pos:
        return "negative", 0.6
    return "neutral", 0.7


def _label_to_standard(label: str) -> str:
    """Normalise FinBERT output labels to lowercase."""
    mapping = {"LABEL_0": "positive", "LABEL_1": "negative", "LABEL_2": "neutral"}
    return mapping.get(label, label.lower())


def analyse_sentiment(news: NewsData) -> tuple[NewsData, SentimentResult]:
    """
    Score every headline and produce an aggregate sentiment result.

    Mutates news.articles in-place (adds label + score to each).
    Returns (updated_news, SentimentResult).
    Never raises — returns error SentimentResult on failure.

    Args:
        news: NewsData from news_data.fetch_news()

    Returns:
        Tuple of (NewsData with scored articles, SentimentResult)
    """
    if not news.articles:
        logger.warning("No articles to analyse for %s", news.symbol)
        return news, SentimentResult(
            overall_label = "neutral",
            overall_score = 0.0,
            article_count = 0,
            error         = news.error or "No articles available",
        )

    logger.info("Analysing sentiment for %d headlines (%s)", len(news.articles), news.symbol)

    with Timer(f"sentiment_{news.symbol}") as t:
        pipe = _get_pipeline()
        pos_count = neu_count = neg_count = 0
        weighted_score = 0.0

        for article in news.articles:
            try:
                if pipe == "fallback" or pipe is None:
                    label, score = _rule_based_sentiment(article.title)
                else:
                    result = pipe(article.title)[0]
                    label  = _label_to_standard(result["label"])
                    score  = round(result["score"], 4)

                article.sentiment_label = label
                article.sentiment_score = score

                if label == "positive":
                    pos_count    += 1
                    weighted_score += score
                elif label == "negative":
                    neg_count    += 1
                    weighted_score -= score
                else:
                    neu_count    += 1

            except Exception as e:
                logger.warning("Sentiment failed for headline '%s': %s", article.title[:50], str(e))
                article.sentiment_label = "neutral"
                article.sentiment_score = 0.5
                neu_count += 1

    total   = len(news.articles)
    net     = weighted_score / total if total else 0.0
    net     = max(-1.0, min(1.0, net))             # clamp to [-1, 1]

    if net > 0.1:
        overall_label = "positive"
    elif net < -0.1:
        overall_label = "negative"
    else:
        overall_label = "neutral"

    result = SentimentResult(
        overall_label    = overall_label,
        overall_score    = round(abs(net), 4),
        positive_count   = pos_count,
        neutral_count    = neu_count,
        negative_count   = neg_count,
        article_count    = total,
        analysis_time_ms = t.elapsed_ms,
    )

    logger.info(
        "Sentiment for %s: %s (score=%.3f) — pos=%d neu=%d neg=%d in %.1fms",
        news.symbol, overall_label, result.overall_score,
        pos_count, neu_count, neg_count, t.elapsed_ms,
    )

    return news, result
