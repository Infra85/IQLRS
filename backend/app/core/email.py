"""Email sending utilities."""

import smtplib
import logging
import ssl
from email.message import EmailMessage

from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """An actionable, public-safe verification email failure."""


def send_otp_email(to_email: str, otp: str):
    if not settings.smtp_email.strip() or not settings.smtp_password.strip():
        logger.error("Verification email unavailable: SMTP_EMAIL or SMTP_PASSWORD is missing")
        raise EmailDeliveryError(
            "Email verification is not configured. Set SMTP_EMAIL and SMTP_PASSWORD on the backend."
        )

    try:
        sender = str(TypeAdapter(EmailStr).validate_python(settings.smtp_email))
        settings.smtp_password.encode("ascii")
    except (ValidationError, UnicodeError):
        logger.error("Verification email unavailable: invalid SMTP configuration")
        raise EmailDeliveryError(
            "Email verification is not configured correctly. Check SMTP_EMAIL and SMTP_PASSWORD on the backend."
        ) from None

    message = EmailMessage()

    message["Subject"] = "Verify your IQLRS account"
    message["From"] = sender
    message["To"] = to_email

    message.set_content(
        f"""
Hello,

Thank you for creating an IQLRS account.

Your email verification OTP is:

{otp}

This OTP will expire in 10 minutes.

If you did not create this account, you can ignore this email.

Regards,
IQLRS Team
"""
    )

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls(context=ssl.create_default_context())
            server.login(sender, settings.smtp_password)
            server.send_message(message)
    except smtplib.SMTPAuthenticationError:
        logger.error("Verification email unavailable: SMTP authentication failed")
        raise EmailDeliveryError(
            "Email verification is unavailable: SMTP authentication failed. "
            "Ask the administrator to check the backend SMTP credentials."
        ) from None
    except (smtplib.SMTPException, OSError):
        # Provider responses can contain credentials or recipient details.
        logger.error("Verification email delivery failed: SMTP or network error")
        raise EmailDeliveryError(
            "Verification email could not be sent. Please try again later or contact the administrator."
        ) from None
