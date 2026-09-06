"""
tests/test_models.py
--------------------
Unit tests for data contracts and models serialization/deserialization.
"""

import unittest
from datetime import datetime
from models import (
    StockData,
    NewsArticle,
    NewsData,
    SentimentResult,
    ResearchReport,
    User,
    UserTable,
    SearchHistoryEntry,
)


class TestModels(unittest.TestCase):

    def test_stock_data_json(self):
        stock = StockData(
            symbol="MSFT",
            company_name="Microsoft Corp",
            current_price=420.5,
            market_cap=3100000000000.0,
        )
        json_str = stock.to_json()
        loaded = StockData.from_json(json_str)
        self.assertEqual(loaded.symbol, "MSFT")
        self.assertEqual(loaded.current_price, 420.5)

    def test_news_data_json(self):
        article = NewsArticle(
            title="Microsoft announces new AI feature",
            publisher="TechNews",
            published_at="2026-08-19 12:00 UTC",
            url="https://example.com/msft-ai",
            sentiment_label="positive",
            sentiment_score=0.95,
        )
        news = NewsData(symbol="MSFT", articles=[article])
        json_str = news.to_json()
        loaded = NewsData.from_json(json_str)

        self.assertEqual(loaded.symbol, "MSFT")
        self.assertEqual(len(loaded.articles), 1)
        self.assertEqual(loaded.articles[0].title, "Microsoft announces new AI feature")
        self.assertEqual(loaded.articles[0].sentiment_label, "positive")

    def test_research_report_defaults(self):
        report = ResearchReport(symbol="TSLA")
        self.assertEqual(report.symbol, "TSLA")
        self.assertIsInstance(report.generated_at, str)
        self.assertEqual(report.errors, [])

    def test_user_from_orm(self):
        user_row = UserTable(
            id=1,
            email="test@example.com",
            hashed_password="hashed_secret_pw",
            amount=5000.50,
            region="India (NSE/BSE)",
            created_at=datetime(2026, 1, 1, 10, 0, 0),
        )
        user_dto = User.from_orm(user_row)
        self.assertEqual(user_dto.id, 1)
        self.assertEqual(user_dto.email, "test@example.com")
        self.assertEqual(user_dto.amount, 5000.50)
        self.assertEqual(user_dto.region, "India (NSE/BSE)")
        self.assertIn("2026-01-01", user_dto.created_at)


if __name__ == "__main__":
    unittest.main()
