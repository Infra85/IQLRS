from datetime import datetime, timedelta, timezone
import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)
from app.core.email import send_otp_email
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter()


# ============================================================
# REGISTER
# ============================================================

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Generate 6-digit OTP
    otp = str(random.randint(100000, 999999))

    # OTP valid for 10 minutes
    otp_expires_at = (
        datetime.now(timezone.utc) + timedelta(minutes=10)
    )

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        email_verified=False,
        otp_code=otp,
        otp_expires_at=otp_expires_at,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Send OTP to user's email
    send_otp_email(user.email, otp)

    return {
        "message": "User registered successfully. "
                   "Please check your email for the OTP.",
        "user_id": str(user.user_id),
    }


# ============================================================
# LOGIN
# ============================================================

@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )

    if not user or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # User must verify email before login
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    # Create JWT using UUID
    access_token = create_access_token(
        data={
            "sub": str(user.user_id),
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


# ============================================================
# VERIFY OTP
# ============================================================

@router.post("/verify-otp")
def verify_otp(
    email: str,
    otp: str,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.email_verified:
        return {
            "message": "Email is already verified",
        }

    if not user.otp_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No OTP found. Please request a new OTP.",
        )

    # Check OTP expiry
    if (
        user.otp_expires_at
        and datetime.now(timezone.utc) > user.otp_expires_at
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP.",
        )

    # Check OTP
    if user.otp_code != otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    # Verify email
    user.email_verified = True
    user.otp_code = None
    user.otp_expires_at = None

    db.commit()

    return {
        "message": "Email verified successfully",
    }
