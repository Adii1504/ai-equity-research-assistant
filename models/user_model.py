"""
models/user_model.py
---------------------
User data contract (dataclass) + SQLAlchemy ORM table for Postgres.

ADR: Why SQLAlchemy over raw psycopg2?
  - ORM gives us a Python object interface instead of hand-written SQL
  - Handles connection pooling automatically
  - Table creation / migrations are declarative and version-controllable
  - Matches the dataclass-first convention already used in stock_model.py
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserTable(Base):
    """SQLAlchemy ORM model — maps to the 'users' table in Postgres."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


@dataclass
class User:
    """
    Plain-data contract used across the app (API responses, etc.).
    Never exposes hashed_password — use UserTable directly for auth checks only.
    """
    id:         int
    email:      str
    created_at: str

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_orm(cls, row: UserTable) -> "User":
        return cls(
            id=row.id,
            email=row.email,
            created_at=row.created_at.isoformat() if row.created_at else "",
        )
