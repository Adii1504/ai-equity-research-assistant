"""
config.py
---------
Single source of truth for all configuration.
Never hardcode values in modules — import from here.
"""

import os
from dotenv import load_dotenv

load_dotenv(override=True)

# ── API Keys ────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")          # newsapi.org free tier

# ── Model Settings ───────────────────────────────────────────────────────────
GROQ_MODEL          = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
FINBERT_MODEL       = "ProsusAI/finbert"               # financial domain BERT
LLM_MAX_TOKENS      = 1024
LLM_TEMPERATURE     = 0.3                              # low = more factual

# ── Cache Settings ───────────────────────────────────────────────────────────
REDIS_HOST          = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT          = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB            = 0
CACHE_TTL_STOCK     = 15 * 60                          # 15 minutes
CACHE_TTL_NEWS      = 30 * 60                          # 30 minutes

# ── Rate Limiting ────────────────────────────────────────────────────────────
MAX_CONCURRENT_REQUESTS = 10                           # asyncio Semaphore limit

# ── Data Settings ────────────────────────────────────────────────────────────
MAX_NEWS_ARTICLES   = 10
NEWS_LOOKBACK_DAYS  = 7

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL           = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT          = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# ── Database (Postgres) ───────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "")

# ── Auth ─────────────────────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_EXPIRE_MINUTES = 60 * 24 * 7   # 7 days

