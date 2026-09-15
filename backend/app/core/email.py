"""Email sending utilities."""

import smtplib
import logging
import ssl
from email.message import EmailMessage
from email.utils import formataddr, formatdate, make_msgid

import httpx
from pydantic import EmailStr, TypeAdapter, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailDeliveryError(Exception):
    """An actionable, public-safe verification email failure."""


def send_otp_email(to_email: str, otp: str):
    production = settings.environment.strip().lower() == "production"
    use_resend = production or bool(settings.resend_api_key.strip())
    if production and not settings.resend_api_key.strip():
        logger.error("Verification email unavailable: RESEND_API_KEY is missing in production")
        raise EmailDeliveryError(
            "Email verification is not configured. Set RESEND_API_KEY on the backend."
        )
    if not use_resend and (not settings.smtp_email.strip() or not settings.smtp_password.strip()):
        logger.error("Verification email unavailable: SMTP_EMAIL or SMTP_PASSWORD is missing")
        raise EmailDeliveryError(
            "Email verification is not configured. Set SMTP_EMAIL and SMTP_PASSWORD on the backend."
        )

    try:
        sender = str(TypeAdapter(EmailStr).validate_python(settings.smtp_email))
        if not use_resend:
            settings.smtp_password.encode("ascii")
    except (ValidationError, UnicodeError):
        logger.error("Verification email unavailable: invalid SMTP configuration")
        raise EmailDeliveryError(
            "Email verification is not configured correctly. Check SMTP_EMAIL and SMTP_PASSWORD on the backend."
        ) from None

    message = EmailMessage()

    message["Subject"] = "Verify your IQLRS account"
    message["From"] = formataddr(("IQLRS", sender))
    message["Date"] = formatdate(localtime=False)
    message["Message-ID"] = make_msgid(domain=sender.split("@")[1])
    message["Auto-Submitted"] = "auto-generated"
    if settings.smtp_reply_to:
        try:
            message["Reply-To"] = str(TypeAdapter(EmailStr).validate_python(settings.smtp_reply_to))
        except ValidationError:
            raise EmailDeliveryError("Email reply-to configuration is invalid.") from None
    message["To"] = to_email

    message.set_content(
        f"""
Hello,

Thank you for creating an IQLRS account.

Your email verification OTP is:

{otp}

This code expires in 10 minutes. Enter it only on the IQLRS verification page.
Never share this code. IQLRS staff will never ask you for it.

If you did not create this account, you can ignore this email.

Regards,
IQLRS Team
"""
    )

    if use_resend:
        payload = {
            "from": message["From"],
            "to": [to_email],
            "subject": message["Subject"],
            "text": message.get_content(),
        }
        if message["Reply-To"]:
            payload["reply_to"] = message["Reply-To"]
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    "https://api.resend.com/emails",
                    headers={"Authorization": f"Bearer {settings.resend_api_key}", "Content-Type": "application/json"},
                    json=payload,
                )
                response.raise_for_status()
            return
        except httpx.HTTPStatusError as exc:
            logger.error("Verification email delivery failed: Resend returned HTTP %s", exc.response.status_code)
            raise EmailDeliveryError(
                "Verification email could not be sent. Please try again later or contact the administrator."
            ) from None
        except httpx.RequestError as exc:
            logger.error("Verification email delivery failed: Resend network error (%s)", type(exc).__name__)
            raise EmailDeliveryError(
                "Verification email could not be sent. Please try again later or contact the administrator."
            ) from None

    try:
        with (smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10, context=ssl.create_default_context())
              if settings.smtp_ssl else smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)) as server:
            if not settings.smtp_ssl:
                server.starttls(context=ssl.create_default_context())
            server.login(settings.smtp_username or sender, settings.smtp_password)
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
