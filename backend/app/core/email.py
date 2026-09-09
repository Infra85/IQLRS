"""Email sending utilities."""

import smtplib
from email.message import EmailMessage

from app.core.config import settings


def send_otp_email(to_email: str, otp: str):
    message = EmailMessage()

    message["Subject"] = "Verify your IQLRS account"
    message["From"] = settings.smtp_email
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

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(
            settings.smtp_email,
            settings.smtp_password,
        )
        server.send_message(message)