"""
tests/test_sentiment.py
-----------------------
Unit tests for sentiment analysis and fallback logic.
"""

import unittest
from unittest.mock import patch
from analysis.sentiment import _rule_based_sentiment, _label_to_standard, analyse_sentiment
from models import NewsData, NewsArticle


class TestSentiment(unittest.TestCase):

    def test_rule_based_positive(self):
        label, score = _rule_based_sentiment("Company beats earnings expectations record profit")
        self.assertEqual(label, "positive")
        self.assertGreater(score, 0.5)

    def test_rule_based_negative(self):
        label, score = _rule_based_sentiment("Layoff cuts announced earnings loss decline")
        self.assertEqual(label, "negative")
        self.assertGreater(score, 0.5)

    def test_label_normalisation(self):
        self.assertEqual(_label_to_standard("LABEL_0"), "positive")
        self.assertEqual(_label_to_standard("LABEL_1"), "negative")
        self.assertEqual(_label_to_standard("LABEL_2"), "neutral")

    def test_analyse_sentiment_empty(self):
        news = NewsData(symbol="EMPTY", articles=[])
        updated_news, result = analyse_sentiment(news)
        self.assertEqual(result.overall_label, "neutral")
        self.assertEqual(result.article_count, 0)

    @patch("analysis.sentiment._get_pipeline", return_value="fallback")
    def test_analyse_sentiment_with_articles(self, mock_pipeline):
        articles = [
            NewsArticle(
                title="Company beats revenue estimates with record profit",
                publisher="Bloomberg",
                published_at="2026-08-19",
                url="https://example.com/1",
            ),
            NewsArticle(
                title="Stock surge continues following strong quarter",
                publisher="Reuters",
                published_at="2026-08-19",
                url="https://example.com/2",
            ),
        ]
        news = NewsData(symbol="GOOD", articles=articles)
        updated_news, result = analyse_sentiment(news)
        self.assertEqual(result.overall_label, "positive")
        self.assertEqual(result.article_count, 2)


if __name__ == "__main__":
    unittest.main()
