"""
utils/db.py
-----------
Postgres connection + session management via SQLAlchemy.

Mirrors utils/cache.py's pattern: a single shared instance ('cache' there,
engine/SessionLocal here) that the rest of the app imports and reuses.

Run once (or let it auto-run on startup) to create tables:
    from utils.db import Base, engine
    Base.metadata.create_all(bind=engine)
"""

import os
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import DATABASE_URL
from models.user_model import Base
from utils.logger import get_logger

logger = get_logger(__name__)

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None
db_available = bool(engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a DB session and guarantees it closes.
    Raises 503 if Postgres is not configured or unreachable.
    """
    if SessionLocal is None or not db_available:
        init_db()

    if SessionLocal is None or not db_available:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Database unavailable — set DATABASE_URL and ensure Postgres is running",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_optional() -> Generator[Optional[Session], None, None]:
    """Like get_db(), but yields None when Postgres is unavailable (never raises)."""
    if SessionLocal is None or not db_available:
        init_db()

    if SessionLocal is None or not db_available:
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist yet. Safe to call on every startup."""
    global engine, SessionLocal, db_available

    import config
    db_url = config.DATABASE_URL or os.getenv("DATABASE_URL", "")

    if not db_url:
        logger.warning("DATABASE_URL not set — skipping Postgres table creation")
        db_available = False
        return

    # Register SearchHistory (and any future models) on Base.metadata
    import models.search_model  # noqa: F401

    try:
        if engine is None or str(engine.url) != db_url:
            engine = create_engine(db_url, pool_pre_ping=True)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)
        db_available = True
        logger.info("Postgres tables verified/created")
    except Exception as exc:
        db_available = False
        logger.warning(
            "Postgres unavailable (%s) — auth and search history disabled. "
            "Core research still works without a database.",
            exc,
        )
