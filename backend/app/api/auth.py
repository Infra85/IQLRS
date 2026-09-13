from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timedelta
import secrets

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.email import EmailDeliveryError, send_otp_email
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == payload.email).with_for_update().first()

    if existing_user and (
        existing_user.email_verified
        or not verify_password(payload.password, existing_user.hashed_password)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    otp = str(secrets.randbelow(900000) + 100000)
    otp_expires_at = datetime.utcnow() + timedelta(minutes=10)

    # Retry legacy unverified registrations only with the original password.
    # Do not replace account details or invalidate the old OTP on delivery failure.
    user = existing_user or User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        name=payload.name,
        email_verified=False,
        otp_code=otp,
        otp_expires_at=otp_expires_at,
    )

    user.otp_code = otp
    user.otp_expires_at = otp_expires_at
    db.add(user)
    try:
        # Enforce uniqueness before sending, but persist only after SMTP accepts.
        db.flush()
        user_id = user.id
        send_otp_email(user.email, otp)
        db.commit()
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from None
    except IntegrityError:
        db.rollback()
        # A concurrent registration can win the unique email constraint.
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=400, detail="Email already registered") from None
        raise

    return {
        "message": "User registered successfully",
        "user_id": user_id,
    }


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(
        payload.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in",
        )

    access_token = create_access_token(
        data={"sub": str(user.id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/verify-otp")
def verify_otp(
    email: str,
    otp: str,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == email).first()

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

    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP.",
        )

    if user.otp_code != otp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    user.email_verified = True
    user.otp_code = None
    user.otp_expires_at = None

    db.commit()

    return {
        "message": "Email verified successfully",
    }
