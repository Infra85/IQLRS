from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from datetime import datetime, timedelta, timezone
import secrets

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token, hash_otp
from app.core.email import EmailDeliveryError, send_otp_email
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, VerifyOTPRequest

from app.core.rate_limit import limit_requests

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, dependencies=[Depends(limit_requests("register", 10, 600))])
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
):
    existing_user = db.query(User).filter(User.email == payload.email).with_for_update().first()

    if existing_user and (
        existing_user.email_verified
        or not verify_password(payload.password, existing_user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    if existing_user and existing_user.otp_expires_at and existing_user.otp_expires_at > datetime.now(timezone.utc) + timedelta(minutes=9):
        raise HTTPException(429, "Please wait one minute before requesting another code.")

    if existing_user is None and len(payload.password) < 12:
        raise HTTPException(422, "New accounts require a password of at least 12 characters.")

    otp = str(secrets.randbelow(900000) + 100000)
    otp_expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

 
    user = existing_user or User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        name=payload.name,
        email_verified=False,
        otp_code=hash_otp(payload.email, otp),
        otp_expires_at=otp_expires_at,
    )

    user.otp_code = hash_otp(payload.email, otp)
    user.otp_attempts = 0
    user.otp_expires_at = otp_expires_at
    db.add(user)
    try:
       
        db.flush()
        user_id = user.user_id
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
        "user_id": str(user_id),
    }


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_requests("login", 30, 300))])
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(
        payload.password,
        user.password_hash,
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
        data={"sub": str(user.user_id)}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/verify-otp", dependencies=[Depends(limit_requests("verify", 30, 300))])
def verify_otp(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db),
):
    email, otp = payload.email, payload.otp
    user = db.query(User).filter(User.email == email).with_for_update().first()

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

    if not user.otp_expires_at or datetime.now(timezone.utc) > user.otp_expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP.",
        )

    if user.otp_attempts >= 5:
        raise HTTPException(429, "Too many attempts. Request a new code.")
    if not secrets.compare_digest(user.otp_code, hash_otp(email, otp)):
        user.otp_attempts += 1
        db.commit()
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
