"""
models/search_model.py
-----------------------
Tracks which symbols a logged-in user has researched.
Used by the recommendation engine to weight suggestions toward
sectors/symbols the user has shown interest in.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey

from models.user_model import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    symbol      = Column(String, nullable=False)
    sector      = Column(String, nullable=True)
    searched_at = Column(DateTime, default=datetime.utcnow)


@dataclass
class SearchHistoryEntry:
    symbol: str
    sector: str
    searched_at: str