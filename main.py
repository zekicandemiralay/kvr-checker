#!/usr/bin/env python3
"""
KVR Munich Emergency Appointment Checker
Polls every CHECK_INTERVAL seconds and notifies via email and/or Telegram.

Usage:
    1. cp .env.example .env   # fill in your credentials
    2. pip install -r requirements.txt
    3. python main.py
"""

import os
import sys
import time
import logging
from pathlib import Path

from dotenv import load_dotenv

import altcha
import checker
import notifier

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main() -> None:
    # Load .env from the same directory as this script
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        log.error(".env file not found. Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)
    load_dotenv(env_path)

    # Require at least one notification channel
    has_email    = notifier.email_configured()
    has_telegram = notifier.telegram_configured()

    if not has_email and not has_telegram:
        log.error(
            "No notification channel configured. "
            "Set email vars (EMAIL_FROM / EMAIL_TO / EMAIL_PASSWORD) "
            "and/or Telegram vars (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID) in .env"
        )
        sys.exit(1)

    channels = []
    if has_email:    channels.append("email")
    if has_telegram: channels.append("telegram")
    log.info("Notifiers active: %s", ", ".join(channels))

    interval = int(os.environ.get("CHECK_INTERVAL", "60"))
    log.info("KVR checker started — polling every %d seconds", interval)
    log.info("Booking URL: %s", checker.BOOKING_URL)

    # Send startup notification so you know it's live
    sent = notifier.notify_startup(interval)
    if sent:
        log.info("Startup notification sent via: %s", ", ".join(sent))
    else:
        log.warning("Startup notification could not be sent — check your credentials.")

    while True:
        try:
            log.info("Fetching ALTCHA challenge...")
            token = altcha.get_captcha_token()
            log.info("ALTCHA solved, checking appointments...")

            available, dates = checker.check_appointments(token)

            if available:
                log.warning("*** APPOINTMENT(S) FOUND: %s ***", dates)
                sent = notifier.notify_appointment_found(dates)
                if sent:
                    log.info("Notifications sent via: %s", ", ".join(sent))
                else:
                    log.error("All notification channels failed!")
            else:
                log.info("No appointments available.")

        except KeyboardInterrupt:
            log.info("Stopped by user.")
            break
        except Exception as err:
            log.error("Error during check: %s", err)

        log.info("Waiting %d seconds before next check...", interval)
        time.sleep(interval)


if __name__ == "__main__":
    main()
