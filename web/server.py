"""
web/server.py
-------------
FastAPI web server — serves the browser UI and exposes the research API.

Uses the existing pipeline unchanged:
  app.research()  →  data/  →  analysis/

# Run:
#     uvicorn web.server:app --host 0.0.0.0 --port 8080 --reload
#
# Open: http://localhost:8080
"""

import sys
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

# Project root on path so existing modules import without modification
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import run_research as run_research_pipeline  # noqa: E402
from models.stock_model import ResearchReport  # noqa: E402
from models.search_model import SearchHistory  # noqa: E402
from utils.cache import cache  # noqa: E402
from utils.db import init_db, get_db_optional  # noqa: E402
from data.stocks_catalog import get_sector_for_symbol  # noqa: E402
from web.auth import router as auth_router, get_current_user_optional  # noqa: E402
from web.catalog import router as catalog_router  # noqa: E402

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="AI Equity Research Assistant",
    description="Web API for automated equity research",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(catalog_router, prefix="/api", tags=["catalog"])


@app.on_event("startup")
async def on_startup():
    init_db()


class ResearchRequest(BaseModel):
    symbols: List[str] = Field(..., min_length=1, max_length=5)


def _to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: _to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [_to_dict(i) for i in obj]
    return obj


def _fetch_price_history(symbol: str) -> List[dict]:
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


def _enrich_report(report: ResearchReport) -> dict:
    data = _to_dict(report)
    data["price_history"] = _fetch_price_history(report.symbol)

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


@app.get("/style.css")
async def serve_css():
    return FileResponse(STATIC_DIR / "style.css", media_type="text/css")


@app.get("/app.js")
async def serve_js():
    return FileResponse(STATIC_DIR / "app.js", media_type="application/javascript")


@app.get("/health")
async def health():
    import utils.db as db_module
    if not db_module.db_available:
        db_module.init_db()
    return {"status": "ok", "redis": cache.is_available, "database": db_module.db_available}


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
    reports = await run_research_pipeline(symbols)

    if current_user and db is not None:
        for symbol in symbols:
            db.add(SearchHistory(
                user_id=current_user.id,
                symbol=symbol,
                sector=get_sector_for_symbol(symbol),
            ))
        db.commit()

    return {"reports": [_enrich_report(r) for r in reports]}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")