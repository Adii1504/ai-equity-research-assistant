"""
web/auth.py
-----------
Signup / login / profile / account funds & region routes.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from config import JWT_SECRET, JWT_EXPIRE_MINUTES
from models import User, UserTable, SearchHistory
from utils import db as db_module
from utils import get_db, get_db_optional, get_logger

logger = get_logger(__name__)
router = APIRouter()


def _hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode("utf-8"))
    except Exception:
        return False


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    region: Optional[str] = "India"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AmountRequest(BaseModel):
    amount: float = Field(..., ge=0, description="Amount in Rupees (₹)")


class AddFundsRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Amount to deposit in Rupees (₹)")


class RegionRequest(BaseModel):
    region: str = Field(..., min_length=1, max_length=100, description="User operating region / country")


class ProfileUpdateRequest(BaseModel):
    amount: Optional[float] = Field(None, ge=0)
    region: Optional[str] = Field(None, max_length=100)


class AuthResponse(BaseModel):
    token: str
    user: dict


def _make_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def _decode_token(authorization: Optional[str]) -> Optional[int]:
    """Returns the user_id from a 'Bearer <token>' header, or None if missing/invalid."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return int(payload["sub"])
    except Exception:
        return None


def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Optional[Session] = Depends(get_db_optional),
) -> Optional[UserTable]:
    """Returns the UserTable row if a valid token was sent, else None. Never raises."""
    if db is None:
        return None
    user_id = _decode_token(authorization)
    if user_id is None:
        return None
    return db.query(UserTable).filter(UserTable.id == user_id).first()


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> UserTable:
    """Returns the UserTable row, or raises 401 if not authenticated."""
    user = get_current_user_optional(authorization, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


@router.post("/signup", response_model=AuthResponse)
async def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if not db_module.db_available:
        raise HTTPException(status_code=503, detail="Database unavailable — cannot sign up")
    existing = db.query(UserTable).filter(UserTable.email == body.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = _hash_password(body.password)
    row = UserTable(
        email=body.email,
        hashed_password=hashed,
        amount=0.0,
        region=body.region or "India",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    logger.info("New user signed up: %s (Region: %s)", body.email, row.region)
    user = User.from_orm(row)
    return AuthResponse(token=_make_token(row.id), user=user.__dict__)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    if not db_module.db_available:
        raise HTTPException(status_code=503, detail="Database unavailable — cannot log in")
    row = db.query(UserTable).filter(UserTable.email == body.email).first()
    if not row or not _verify_password(body.password, row.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    logger.info("User logged in: %s", body.email)
    user = User.from_orm(row)
    return AuthResponse(token=_make_token(row.id), user=user.__dict__)


@router.get("/me")
async def me(current_user: UserTable = Depends(get_current_user)):
    return User.from_orm(current_user).__dict__


@router.post("/region")
@router.put("/region")
async def update_region(
    body: RegionRequest,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the user's region in their PostgreSQL database record."""
    current_user.region = body.region.strip()
    db.commit()
    db.refresh(current_user)
    logger.info("Updated region for %s to '%s'", current_user.email, current_user.region)
    return {
        "status": "ok",
        "region": current_user.region,
        "user": User.from_orm(current_user).__dict__,
    }


@router.post("/amount")
@router.put("/amount")
async def set_amount(
    body: AmountRequest,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Set the total amount/balance in Rupees (₹) in the user's PostgreSQL record."""
    current_user.amount = round(body.amount, 2)
    db.commit()
    db.refresh(current_user)
    logger.info("Updated balance for %s to ₹%.2f", current_user.email, current_user.amount)
    return {
        "status": "ok",
        "amount": current_user.amount,
        "user": User.from_orm(current_user).__dict__,
    }


@router.post("/add-funds")
async def add_funds(
    body: AddFundsRequest,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deposit additional funds in Rupees (₹) into the user's database record."""
    current = float(current_user.amount or 0.0)
    current_user.amount = round(current + body.amount, 2)
    db.commit()
    db.refresh(current_user)
    logger.info("Added ₹%.2f to %s balance (new total: ₹%.2f)", body.amount, current_user.email, current_user.amount)
    return {
        "status": "ok",
        "deposited": body.amount,
        "amount": current_user.amount,
        "user": User.from_orm(current_user).__dict__,
    }


@router.put("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update profile fields (amount, region) in PostgreSQL database."""
    if body.amount is not None:
        current_user.amount = round(body.amount, 2)
    if body.region is not None:
        current_user.region = body.region.strip()

    db.commit()
    db.refresh(current_user)
    return {
        "status": "ok",
        "user": User.from_orm(current_user).__dict__,
    }


@router.get("/history")
async def get_history(
    current_user: UserTable = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == current_user.id)
        .order_by(SearchHistory.searched_at.desc())
        .limit(20)
        .all()
    )
    return {
        "history": [
            {
                "symbol": r.symbol,
                "sector": r.sector,
                "searched_at": r.searched_at.isoformat() if r.searched_at else "",
            }
            for r in records
        ]
    }
