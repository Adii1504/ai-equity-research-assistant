# AI Equity Research Assistant

An automated equity research platform that combines live market data, financial news sentiment, and LLM analysis. Enter one or more tickers (US or Indian markets) and get a structured report with fundamentals, headlines, sentiment scores, and an AI-written research note.

**Two ways to run:**
- **Web app (recommended)** — browser UI at `http://localhost:8080` via FastAPI (`web/`)
- **Streamlit app** — original UI via `streamlit run main.py`

All core pipeline code (`app.py`, `data/`, `analysis/`, `models/`) is shared unchanged between both.

## Features

- **Live stock fundamentals** — price, market cap, P/E, 52-week range, sector (via Yahoo Finance)
- **Recent news headlines** — yfinance feed with optional NewsAPI fallback
- **Financial sentiment analysis** — ProsusAI/FinBERT with rule-based fallback
- **AI research notes** — structured summary, positives, risks, and outlook (Groq Llama 3 70B)
- **30-day price chart** — inline chart per ticker
- **Multi-ticker support** — analyse up to 5 symbols concurrently
- **Redis caching** — 15 min (stock) / 30 min (news) TTL; graceful fallback if Redis is down
- **Partial reports on failure** — if news or LLM fails, stock data and other sections still render

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────────────────┐
│  main.py    │────▶│  app.py (async orchestrator)                     │
│  Streamlit  │     │                                                  │
└─────────────┘     │  Stage 1: stock + news  ── asyncio.gather()    │
                    │  Stage 2: FinBERT sentiment                      │
                    │  Stage 3: Groq LLM report                        │
                    └──────────────────────────────────────────────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              ▼                          ▼                          ▼
      data/stock_data.py         data/news_data.py        analysis/sentiment.py
      (yfinance)                 (yfinance + NewsAPI)     (FinBERT)
                                                                    │
                                                                    ▼
                                                         analysis/report_generator.py
                                                         (Groq API)
```

Engineering decisions (caching, FinBERT vs VADER, Groq, concurrency, graceful degradation) are documented in [docs/adr.md](docs/adr.md).

## Tech Stack

| Layer | Technology |
|-------|------------|
| UI | Streamlit |
| Orchestration | Python asyncio |
| Market data | yfinance |
| News | yfinance, NewsAPI (optional) |
| Sentiment | Hugging Face Transformers (FinBERT) |
| LLM | Groq API (llama-3.3-70b-versatile) |
| Cache | Redis |
| Container | Docker + Docker Compose |

## Prerequisites

- Python 3.11+
- [Groq API key](https://console.groq.com) (required for AI reports)
- [NewsAPI key](https://newsapi.org) (optional — yfinance is the primary news source)
- Redis (optional — app runs without it, just without caching)

## Web Application (Browser UI)

### Quick launch

**npm (recommended):**
```bash
cp .env.example .env          # first time only — set GROQ_API_KEY in .env
npm run setup                 # first time only — install Python deps
npm run dev                   # start at http://localhost:8080
```

**Windows:** double-click or run `start-web.bat`

**Mac / Linux:**
```bash
chmod +x start-web.sh && ./start-web.sh
```

**Manual:**
```bash
pip install -r requirements-web.txt
uvicorn web.server:app --host 0.0.0.0 --port 8080 --reload
```

Open **[http://localhost:8080](http://localhost:8080)** in your browser.

### Docker (web + Redis)

```bash
docker compose -f docker-compose.web.yml up --build
```

App: [http://localhost:8080](http://localhost:8080) · Redis: `localhost:6379`

---

## Quick Start (Streamlit)

### 1. Clone and install

```bash
git clone <your-repo-url>
cd aifinancecla

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set your Groq key:

```env
GROQ_API_KEY=your_groq_api_key_here
```

### 3. (Optional) Start Redis

```bash
docker run -d -p 6379:6379 redis:7-alpine
```

Or use Docker Compose (starts Redis + app together):

```bash
docker compose up --build
```

Then open [http://localhost:8501](http://localhost:8501).

### 4. Run locally

```bash
streamlit run main.py
```

## Usage

1. Open the app in your browser (default: `http://localhost:8501`).
2. Enter one or more tickers, comma-separated (e.g. `AAPL, MSFT, TCS.NS`).
3. Click **Analyse →**.
4. Review metrics, price chart, headlines with sentiment badges, and the AI research note.

**Example tickers:** `AAPL` · `TSLA` · `MSFT` · `TCS.NS` · `RELIANCE.NS` · `INFY.NS`

> **Note:** On first run, FinBERT (~440 MB) downloads from Hugging Face. Subsequent runs reuse the cached model.

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GROQ_API_KEY` | Yes | — | Groq API key for LLM reports |
| `NEWS_API_KEY` | No | — | NewsAPI fallback when yfinance news fails |
| `REDIS_HOST` | No | `localhost` | Redis host |
| `REDIS_PORT` | No | `6379` | Redis port |
| `LOG_LEVEL` | No | `INFO` | Logging level |

See [config.py](config.py) for model names, cache TTLs, and rate limits.

## Project Structure

```
aifinancecla/
├── web/
│   ├── server.py           # FastAPI web server + /api/research
│   └── static/             # Browser UI (HTML, CSS, JS)
├── main.py                 # Streamlit UI (original, unchanged)
├── app.py                  # Async research pipeline orchestrator
├── start-web.bat           # One-click web launcher (Windows)
├── start-web.sh            # One-click web launcher (Mac/Linux)
├── Dockerfile.web          # Docker image for web app
├── docker-compose.web.yml  # Web + Redis stack
├── requirements-web.txt    # Web deps (includes requirements.txt)
├── config.py               # Central configuration
├── data/
│   ├── stock_data.py       # Yahoo Finance fetch + cache
│   └── news_data.py        # News fetch + cache
├── analysis/
│   ├── sentiment.py        # FinBERT sentiment scoring
│   └── report_generator.py # Groq LLM report generation
├── models/
│   └── stock_model.py      # Dataclass contracts (StockData, NewsData, etc.)
├── utils/
│   ├── cache.py            # Redis wrapper with fallback
│   ├── logger.py           # Structured logging
│   └── timer.py            # Latency measurement
├── tests/
│   └── test_stock_data.py  # Unit tests
├── docs/
│   └── adr.md              # Architecture decision records
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Testing

```bash
python -m unittest tests.test_stock_data -v
```

Or with pytest (install separately: `pip install pytest`):

```bash
python -m pytest tests/ -v
```

Tests cover model serialization, mocked stock fetch, graceful degradation, and rule-based sentiment fallback.

## Docker

Build and run the full stack (app + Redis):

```bash
docker compose up --build
```

- App: [http://localhost:8501](http://localhost:8501)
- Redis: `localhost:6379`

Ensure `.env` exists with `GROQ_API_KEY` before starting.

## Performance

Typical cold-cache latency (single ticker):

| Stage | ~Time |
|-------|-------|
| Stock fetch | 1.2 s |
| News fetch | 0.8 s |
| Sentiment (10 headlines) | 0.6 s |
| LLM report | 1.0 s |
| **Total** | **~3.2 s** |

With Redis cache hits, stock + news return in ~180 ms. Multi-ticker requests run concurrently (bounded by `MAX_CONCURRENT_REQUESTS = 10`).


## License

MIT 
