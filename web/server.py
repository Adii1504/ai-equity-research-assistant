"""
web/server.py
-------------
FastAPI web server — serves the browser UI and exposes the research API.

Uses the existing pipeline unchanged:
  app.research()  →  data/  →  analysis/

Run:
    uvicorn web.server:app --host 0.0.0.0 --port 8080 --reload

Open: http://localhost:8080
"""

import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, List

import yfinance as yf
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Project root on path so existing modules import without modification
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import run_research as run_research_pipeline  # noqa: E402
from models.stock_model import ResearchReport  # noqa: E402
from utils.cache import cache  # noqa: E402

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


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "redis": cache.is_available}


@app.post("/api/research")
async def api_research(body: ResearchRequest):
    symbols = [s.strip().upper() for s in body.symbols if s.strip()]
    if not symbols:
        raise HTTPException(status_code=400, detail="Provide at least one ticker symbol")

    symbols = symbols[:5]
    reports = await run_research_pipeline(symbols)
    return {"reports": [_enrich_report(r) for r in reports]}


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
