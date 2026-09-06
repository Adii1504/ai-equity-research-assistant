"""
data/synthetic_data.py
----------------------
Synthetic market data for stocks, mutual funds, and F&O.
This provides instantaneous data to the client to avoid API delays,
while the rest of the application (like actual research) can keep working as usual.
"""

def get_synthetic_market_data():
    return {
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc.", "price": 175.40, "change_pct": 1.2},
            {"symbol": "MSFT", "name": "Microsoft Corp.", "price": 310.20, "change_pct": -0.5},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 135.10, "change_pct": 0.8},
            {"symbol": "RELIANCE.NS", "name": "Reliance Industries", "price": 2450.00, "change_pct": 1.5},
            {"symbol": "TCS.NS", "name": "Tata Consultancy Services", "price": 3400.00, "change_pct": -0.2}
        ],
        "mutual_funds": [
            {"id": "fund_001", "name": "Growth Equity Fund", "nav": 245.67, "returns_1y_pct": 18.4},
            {"id": "fund_002", "name": "Balanced Advantage Fund", "nav": 58.32, "returns_1y_pct": 11.1},
            {"id": "fund_006", "name": "Index Fund - Nifty 50", "nav": 201.55, "returns_1y_pct": 14.7}
        ],
        "fo": [
            {"contract": "NIFTY24MAY15000CE", "type": "Call", "strike": 15000, "premium": 145.20, "change_pct": 5.4},
            {"contract": "BANKNIFTY24MAY35000PE", "type": "Put", "strike": 35000, "premium": 210.50, "change_pct": -2.1},
            {"contract": "RELIANCE24MAY2500CE", "type": "Call", "strike": 2500, "premium": 45.10, "change_pct": 12.0}
        ],
        "features": {
            "intraday": [
                {"symbol": "TSLA", "company": "Tesla Inc", "price": 330.56, "change": 4.2, "volume": "45.2M"},
                {"symbol": "NVDA", "company": "NVIDIA Corp", "price": 148.72, "change": 2.5, "volume": "38.1M"},
                {"symbol": "AAPL", "company": "Apple Inc", "price": 305.93, "change": 1.1, "volume": "22.5M"}
            ],
            "stock-screener": [
                {"symbol": "INFY.NS", "company": "Infosys Ltd.", "rsi": 28.4, "pe": 14.2, "sector": "Technology"},
                {"symbol": "WIPRO.NS", "company": "Wipro Ltd.", "rsi": 29.1, "pe": 13.8, "sector": "Technology"},
                {"symbol": "ITC.NS", "company": "ITC Ltd.", "rsi": 25.6, "pe": 11.5, "sector": "Consumer Goods"}
            ],
            "etf-screener": [
                {"symbol": "XLK", "name": "Technology Select Sector SPDR", "aum": "$50B", "return_1y": "35.2%", "expense": "0.10%"},
                {"symbol": "QQQ", "name": "Invesco QQQ Trust", "aum": "$200B", "return_1y": "38.1%", "expense": "0.20%"},
                {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "aum": "$350B", "return_1y": "15.4%", "expense": "0.03%"}
            ],
            "stock-events": [
                {"symbol": "AAPL", "event": "Dividend", "details": "$0.24 per share", "date": "2026-08-24"},
                {"symbol": "MSFT", "event": "Earnings", "details": "Q3 Results", "date": "2026-08-28"},
                {"symbol": "RELIANCE.NS", "event": "Bonus Issue", "details": "1:1 Ratio", "date": "2026-09-05"}
            ],
            "ipo": [
                {"company": "Stripe", "expected": "Q4 2026", "est_valuation": "$65 Billion", "sector": "Fintech"},
                {"company": "Databricks", "expected": "Q1 2027", "est_valuation": "$43 Billion", "sector": "Enterprise Software"},
                {"company": "SpaceX", "expected": "TBD", "est_valuation": "$150 Billion", "sector": "Aerospace"}
            ],
            "demat-account": {
                "status": "In Progress",
                "progress_pct": 80,
                "next_step": "e-Sign Application",
                "benefits": ["Zero account opening fees", "Free AMC for 1st year", "AI-powered research access"]
            },
            "mtf": {
                "available_margin": 10000,
                "currency": "USD",
                "interest_rate_pa": 8.5,
                "approved_stocks": ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA"]
            },
            "market-today": [
                {"headline": "NIFTY crosses 25,000 mark amidst strong global cues", "sentiment": "bullish", "time": "10:30 AM"},
                {"headline": "Tech sector rallies ahead of major earnings week", "sentiment": "bullish", "time": "11:45 AM"},
                {"headline": "Oil prices dip slightly amid oversupply concerns", "sentiment": "bearish", "time": "01:15 PM"}
            ]
        },
        "schemes": [
            {
                "id": "pm-awas",
                "title": "PM Awas Yojana (Urban)",
                "category": "Housing",
                "eligibility": "Income below ₹18L/yr",
                "benefits": "Interest subsidy up to ₹2.67 Lakhs",
                "link": "#"
            },
            {
                "id": "pm-kisan",
                "title": "PM Kisan Samman Nidhi",
                "category": "Agriculture",
                "eligibility": "Small/marginal farmers",
                "benefits": "₹6,000 per year income support",
                "link": "#"
            },
            {
                "id": "mudra",
                "title": "PMMY (Mudra Yojana)",
                "category": "Business",
                "eligibility": "Micro enterprises",
                "benefits": "Collateral-free loans up to ₹10 Lakhs",
                "link": "#"
            }
        ]
    }
