"""
utils/logger.py
---------------
Centralised logging setup.
Import get_logger() in every module — never use print() in production code.

ADR: Why structured logging?
  - grep-able in production
  - Timestamps + module names for debugging
  - GS Engineering runs 24/7 systems — logs are the only visibility
"""

import logging
import sys
from config import LOG_LEVEL, LOG_FORMAT


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger with consistent formatting.

    Usage:
        logger = get_logger(__name__)
        logger.info("Fetching stock data for AAPL")
        logger.error("Failed to fetch news: %s", str(e))
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        logger.propagate = False

    return logger
