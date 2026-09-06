"""
web/server.py
-------------
FastAPI web server — serves the browser UI and exposes the research & catalog API.
"""

import asyncio
import os
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, List, Optional

import yfinance as yf
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app import run_research as run_research_pipeline
from analysis import warmup_pipeline
from data import get_sector_for_symbol
from models import ResearchReport, SearchHistory
from utils import cache, init_db, get_db_optional, db_available
from web.auth import router as auth_router, get_current_user_optional
from web.catalog import router as catalog_router

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern lifespan handler for startup and shutdown tasks."""
    init_db()
    if os.getenv("TESTING") != "1":
        # Pre-warm FinBERT model in background thread to avoid cold-start lag
        asyncio.create_task(asyncio.to_thread(warmup_pipeline))
    yield


app = FastAPI(
    title="AI Equity Research Assistant",
    description="Web API for automated equity research",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(catalog_router, prefix="/api", tags=["catalog"])


class ResearchRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1, max_length=5)


class SchemeRequest(BaseModel):
    profile: Optional[dict] = None


def _to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: _to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    return obj


def _fetch_price_history_sync(symbol: str) -> List[dict]:
    try:
        hist = yf.Ticker(symbol).history(period="1mo")
        if hist.empty:
            return []
        return [
            {"date": idx.strftime("%Y-%m-%d"), "price": round(float(row["Close"]), 2)}
            for idx, row in hist.iterrows()
        ]
    except Exception:
        return []


async def _fetch_price_history_async(symbol: str) -> List[dict]:
    return await asyncio.to_thread(_fetch_price_history_sync, symbol)


def _enrich_report_data(report: ResearchReport, price_hist: List[dict]) -> dict:
    data = _to_dict(report)
    data["price_history"] = price_hist

    stock = report.stock
    if stock and stock.from_cache:
        remaining = cache.ttl(f"stock:{report.symbol}")
        data["cache_info"] = {"stock_ttl_seconds": remaining, "from_cache": True}
    elif report.news and report.news.from_cache:
        data["cache_info"] = {"from_cache": True}
    else:
        data["cache_info"] = {"from_cache": False}

    return data


# ── Page routes ──────────────────────────────────────────────────────────────
@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/stocks")
async def stocks_page():
    return FileResponse(STATIC_DIR / "stocks.html")


@app.get("/mutual-funds")
async def funds_page():
    return FileResponse(STATIC_DIR / "funds.html")


@app.get("/recommend")
async def recommend_page():
    return FileResponse(STATIC_DIR / "recommend.html")


@app.get("/profile")
async def profile_page():
    return FileResponse(STATIC_DIR / "profile.html")


# ── Root static file fallbacks (for clean relative frontend URLs) ────────────
@app.get("/style.css")
async def serve_css():
    return FileResponse(STATIC_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


@app.get("/helpers.js")
async def serve_helpers_js():
    return FileResponse(STATIC_DIR / "helpers.js", media_type="application/javascript")


@app.get("/profile.js")
async def serve_profile_js():
    return FileResponse(STATIC_DIR / "profile.js", media_type="application/javascript")


@app.get("/logo.png")
async def serve_logo():
    return FileResponse(STATIC_DIR / "logo.png", media_type="image/png")


@app.get("/hero-banner.jpg")
async def serve_hero_banner():
    return FileResponse(STATIC_DIR / "hero-banner.jpg", media_type="image/jpeg")


# ── Health & Utility routes ──────────────────────────────────────────────────
@app.get("/health")
async def health():
    import utils.db as db_module
    if not db_module.db_available:
        db_module.init_db()
    return {"status": "ok", "redis": cache.is_available, "database": db_module.db_available}


@app.post("/find-schemes")
async def find_schemes(body: SchemeRequest):
    """Provide tailored investment schemes and AI insights for profile dashboard."""
    schemes = [
        {
            "name": "Tax Saving Equity Linked Scheme (ELSS)",
            "explanation": "High growth potential with Section 80C tax deduction benefits and a 3-year lock-in period.",
        },
        {
            "name": "Systematic Equity Allocation (Nifty 50 Index)",
            "explanation": "Low-cost, diversified index investing suitable for long-term wealth compounding.",
        },
        {
            "name": "Dynamic Asset Allocation / Balanced Advantage",
            "explanation": "Automatically balances debt and equity allocation to mitigate downside risk during volatile market regimes.",
        },
    ]
    return {"schemes": schemes}


# ── API routes ───────────────────────────────────────────────────────────────
@app.post("/api/research")
async def api_research(
    body: ResearchRequest,
    current_user: Optional[object] = Depends(get_current_user_optional),
    db: Optional[Session] = Depends(get_db_optional),
):
    symbols = [s.strip().upper() for s in body.symbols if s.strip()]
    if not symbols:
        raise HTTPException(status_code=400, detail="Provide at least one ticker symbol")

    symbols = symbols[:5]

    # Run research pipeline AND price history fetches concurrently
    reports_task = run_research_pipeline(symbols)
    histories_task = asyncio.gather(*[_fetch_price_history_async(s) for s in symbols])

    reports, histories = await asyncio.gather(reports_task, histories_task)

    if current_user and db is not None:
        for symbol in symbols:
            db.add(
                SearchHistory(
                    user_id=getattr(current_user, "id", None),
                    symbol=symbol,
                    sector=get_sector_for_symbol(symbol),
                )
            )
        try:
            db.commit()
        except Exception:
            db.rollback()

    enriched_reports = [
        _enrich_report_data(report, hist)
        for report, hist in zip(reports, histories)
    ]
    return {"reports": enriched_reports}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")