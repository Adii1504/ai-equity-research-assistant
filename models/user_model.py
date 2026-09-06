"""
models/user_model.py
---------------------
User data contract (dataclass) + SQLAlchemy ORM table for Postgres.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UserTable(Base):
    """SQLAlchemy ORM model — maps to the 'users' table in Postgres."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    amount          = Column(Float, default=0.0, nullable=False)
    region          = Column(String, default="India", nullable=True)
    created_at      = Column(DateTime, default=lambda: datetime.now(timezone.utc))


@dataclass
class User:
    """
    Plain-data contract used across the app (API responses, etc.).
    Never exposes hashed_password — use UserTable directly for auth checks only.
    """
    id:         int
    email:      str
    amount:     float = 0.0
    region:     str   = "India"
    created_at: str   = ""

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_orm(cls, row: UserTable) -> "User":
        return cls(
            id=row.id,
            email=row.email,
            amount=round(float(getattr(row, "amount", 0.0) or 0.0), 2),
            region=str(getattr(row, "region", "India") or "India"),
            created_at=row.created_at.isoformat() if row.created_at else "",
        )
