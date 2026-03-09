"""
Email notification via SMTP.
Reads config from environment variables (loaded via .env).
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BOOKING_URL = (
    "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html"
    "#/services/10339027/locations/10187259"
)


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


def notify_appointment_found(dates: list) -> None:
    dates_str = "\n".join(f"  - {d}" for d in dates) if dates else "  (check the website)"
    body = (
        "APPOINTMENT AVAILABLE at Munich KVR!\n"
        "======================================\n\n"
        f"Available dates:\n{dates_str}\n\n"
        "Book NOW (slots go fast):\n"
        f"{BOOKING_URL}\n\n"
        "Service: Notfall-Hilfe Aufenthaltstitel\n"
        "Location: Servicestelle für Zuwanderung und Einbürgerung\n"
        "         Ruppertstraße 19, Munich\n"
    )
    send_email("🚨 KVR Munich: Appointment Available!", body)
