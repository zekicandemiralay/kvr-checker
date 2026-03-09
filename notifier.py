"""
Notification channels: Email (SMTP) and Telegram.
Both are optional — whichever vars are set in .env will be used.
At least one must be configured (enforced in main.py).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

BOOKING_URL = (
    "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html"
    "#/services/10339027/locations/10187259"
)


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(subject: str, body: str) -> None:
    email_from = os.environ["EMAIL_FROM"]
    email_to   = os.environ["EMAIL_TO"]
    password   = os.environ["EMAIL_PASSWORD"]
    smtp_host  = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port  = int(os.environ.get("SMTP_PORT", "587"))

    msg = MIMEMultipart()
    msg["From"]    = email_from
    msg["To"]      = email_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.ehlo()
        server.starttls()
        server.login(email_from, password)
        server.send_message(msg)


def email_configured() -> bool:
    return all(os.environ.get(v) for v in ("EMAIL_FROM", "EMAIL_TO", "EMAIL_PASSWORD"))


# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------

def send_telegram(text: str) -> None:
    token   = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    resp = requests.get(
        f"https://api.telegram.org/bot{token}/sendMessage",
        params={"chat_id": chat_id, "text": text},
        timeout=10,
    )
    resp.raise_for_status()


def telegram_configured() -> bool:
    return all(os.environ.get(v) for v in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"))


# ---------------------------------------------------------------------------
# Combined alert
# ---------------------------------------------------------------------------

def notify_appointment_found(dates: list) -> list[str]:
    """
    Send alerts via all configured channels.
    Returns list of channels that succeeded.
    """
    dates_str = "\n".join(f"  - {d}" for d in dates) if dates else "  (check the website)"

    long_body = (
        "APPOINTMENT AVAILABLE at Munich KVR!\n"
        "======================================\n\n"
        f"Available dates:\n{dates_str}\n\n"
        "Book NOW (slots go fast):\n"
        f"{BOOKING_URL}\n\n"
        "Service: Notfall-Hilfe Aufenthaltstitel\n"
        "Location: Servicestelle für Zuwanderung und Einbürgerung\n"
        "         Ruppertstraße 19, Munich\n"
    )

    tg_text = (
        "🚨 KVR Munich: APPOINTMENT AVAILABLE!\n\n"
        f"Dates:\n{dates_str}\n\n"
        f"Book NOW: {BOOKING_URL}"
    )

    sent = []

    if email_configured():
        try:
            send_email("🚨 KVR Munich: Appointment Available!", long_body)
            sent.append("email")
        except Exception as e:
            print(f"[notifier] Email failed: {e}")

    if telegram_configured():
        try:
            send_telegram(tg_text)
            sent.append("telegram")
        except Exception as e:
            print(f"[notifier] Telegram failed: {e}")

    return sent
