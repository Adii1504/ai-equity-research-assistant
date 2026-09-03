"""
web/catalog.py
----------------
Routes for:
  GET /api/stocks     — curated stock catalog (for the Stocks page)
  GET /api/funds      — mock mutual fund list (for the Mutual Funds page)
  GET /api/recommend  — combined rule-based + history-based recommendations

ADR: Recommendation scoring
  Rule-based signals (always applied):
    + recent price momentum (price_change_pct)
    + reasonable valuation (P/E between 5 and 40)
    - extreme/unavailable valuation
  History-based signals (only if logged in, from search_history table):
    + symbol previously searched directly
    + sector previously searched (even if this exact symbol wasn't)

  This keeps recommendations sane for anonymous users (pure rules) while
  personalising for logged-in users without needing a heavy ML model.
"""

from collections import Counter
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.stocks_catalog import get_stock_catalog
from data.funds_data import get_mock_funds
from data.stock_data import fetch_stock_data
from models.user_model import UserTable
from models.search_model import SearchHistory
from utils.db import get_db_optional
from utils.logger import get_logger
from web.auth import get_current_user_optional

logger = get_logger(__name__)
router = APIRouter()


@router.get("/stocks")
async def list_stocks():
    return {"stocks": get_stock_catalog()}


@router.get("/funds")
async def list_funds():
    return {"funds": get_mock_funds()}


def _rule_score(stock) -> float:
    if stock is None:
        return -100.0  # unfetchable — push to the bottom, don't recommend blind

    score = 0.0
    if stock.price_change_pct is not None:
        score += stock.price_change_pct  # reward recent positive momentum

    if stock.pe_ratio is not None:
        if 5 <= stock.pe_ratio <= 40:
            score += 5
        else:
            score -= 5
    # missing P/E: neutral, no penalty — some sectors/stocks legitimately lack it

    return score


def _history_boost(symbol: str, sector: str, searched_symbols: Counter, searched_sectors: Counter) -> float:
    boost = 0.0
    if searched_symbols.get(symbol, 0) > 0:
        boost += 10  # user has directly researched this exact stock before
    if searched_sectors.get(sector, 0) > 0:
        boost += 5   # user has shown interest in this sector
    return boost


@router.get("/recommend")
async def recommend(
    limit: int = 5,
    current_user: Optional[UserTable] = Depends(get_current_user_optional),
    db: Optional[Session] = Depends(get_db_optional),
):
    catalog = get_stock_catalog()

    searched_symbols: Counter = Counter()
    searched_sectors: Counter = Counter()
    personalised = False

    if current_user and db is not None:
        history: List[SearchHistory] = (
            db.query(SearchHistory)
            .filter(SearchHistory.user_id == current_user.id)
            .all()
        )
        if history:
            personalised = True
            searched_symbols.update(h.symbol for h in history)
            searched_sectors.update(h.sector for h in history if h.sector)

    results: List[Dict] = []
    for item in catalog:
        symbol = item["symbol"]
        sector = item["sector"]
        try:
            stock = fetch_stock_data(symbol)
        except Exception as e:
            logger.warning("Recommend: fetch failed for %s: %s", symbol, str(e))
            stock = None

        base = _rule_score(stock)
        boost = _history_boost(symbol, sector, searched_symbols, searched_sectors)
        total = base + boost

        reasons = []
        if stock and stock.price_change_pct is not None and stock.price_change_pct > 0:
            reasons.append(f"positive momentum ({stock.price_change_pct:+.2f}% today)")
        if stock and stock.pe_ratio is not None and 5 <= stock.pe_ratio <= 40:
            reasons.append(f"reasonable valuation (P/E {stock.pe_ratio:.1f}x)")
        if searched_symbols.get(symbol, 0) > 0:
            reasons.append("you've researched this stock before")
        elif searched_sectors.get(sector, 0) > 0:
            reasons.append(f"matches your interest in {sector}")
        if not reasons:
            reasons.append("included from the general catalog")

        results.append({
            "symbol": symbol,
            "name": item["name"],
            "sector": sector,
            "score": round(total, 2),
            "current_price": stock.current_price if stock else None,
            "price_change_pct": stock.price_change_pct if stock else None,
            "pe_ratio": stock.pe_ratio if stock else None,
            "reasons": reasons,
        })

    results.sort(key=lambda r: r["score"], reverse=True)

    return {
        "personalised": personalised,
        "recommendations": results[:limit],
    }