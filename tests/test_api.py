"""
tests/test_api.py
-----------------
Integration tests for FastAPI endpoints using TestClient.
"""

import os
import unittest
from unittest.mock import patch

# Disable database and background warmup during test suite
os.environ["DATABASE_URL"] = ""
os.environ["TESTING"] = "1"

from fastapi.testclient import TestClient
from web.server import app
from models import StockData


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")

    def test_stocks_catalog_endpoint(self):
        response = self.client.get("/api/stocks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("stocks", data)
        self.assertGreater(len(data["stocks"]), 0)

    def test_funds_catalog_endpoint(self):
        response = self.client.get("/api/funds")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("funds", data)
        self.assertGreater(len(data["funds"]), 0)

    @patch("web.catalog.fetch_stock_data")
    def test_recommend_endpoint(self, mock_fetch):
        mock_fetch.return_value = StockData(
            symbol="AAPL",
            company_name="Apple Inc.",
            current_price=190.0,
            price_change_pct=1.5,
            pe_ratio=25.0,
        )
        response = self.client.get("/api/recommend?limit=3")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommendations", data)
        self.assertLessEqual(len(data["recommendations"]), 3)

    def test_find_schemes_endpoint(self):
        response = self.client.post("/find-schemes", json={"profile": {"income": "100000"}})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("schemes", data)
        self.assertGreater(len(data["schemes"]), 0)

    def test_static_pages_serve(self):
        for route in ["/", "/stocks", "/mutual-funds", "/recommend", "/profile"]:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Route {route} failed")


if __name__ == "__main__":
    unittest.main()
