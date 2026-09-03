"""
data/funds_data.py
--------------------
Mock mutual fund data.

ADR: Why mock data for mutual funds?
  - No free/reliable mutual fund API was selected yet for this project
  - This keeps the fund page and API contract fully working now
  - Swapping in a real source later only means replacing get_mock_funds()
    with a real fetch — the API route and frontend stay unchanged
"""

from typing import List, Dict

_MOCK_FUNDS: List[Dict] = [
    {
        "id": "fund_001",
        "name": "Growth Equity Fund",
        "category": "Large Cap",
        "nav": 245.67,
        "returns_1y_pct": 18.4,
        "returns_3y_pct": 14.2,
        "risk": "Moderate",
        "expense_ratio_pct": 0.8,
    },
    {
        "id": "fund_002",
        "name": "Balanced Advantage Fund",
        "category": "Hybrid",
        "nav": 58.32,
        "returns_1y_pct": 11.1,
        "returns_3y_pct": 9.6,
        "risk": "Low-Moderate",
        "expense_ratio_pct": 0.6,
    },
    {
        "id": "fund_003",
        "name": "Small Cap Opportunities Fund",
        "category": "Small Cap",
        "nav": 89.14,
        "returns_1y_pct": 27.8,
        "returns_3y_pct": 19.5,
        "risk": "High",
        "expense_ratio_pct": 1.1,
    },
    {
        "id": "fund_004",
        "name": "Technology Sector Fund",
        "category": "Sectoral - Technology",
        "nav": 132.90,
        "returns_1y_pct": 22.3,
        "returns_3y_pct": 20.1,
        "risk": "High",
        "expense_ratio_pct": 0.95,
    },
    {
        "id": "fund_005",
        "name": "Fixed Income Bond Fund",
        "category": "Debt",
        "nav": 32.45,
        "returns_1y_pct": 6.9,
        "returns_3y_pct": 6.2,
        "risk": "Low",
        "expense_ratio_pct": 0.4,
    },
    {
        "id": "fund_006",
        "name": "Index Fund - Nifty 50",
        "category": "Index",
        "nav": 201.55,
        "returns_1y_pct": 14.7,
        "returns_3y_pct": 12.9,
        "risk": "Moderate",
        "expense_ratio_pct": 0.2,
    },
]


def get_mock_funds() -> List[Dict]:
    return _MOCK_FUNDS