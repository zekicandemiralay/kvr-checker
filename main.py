#!/usr/bin/env python3
"""
KVR Munich Emergency Appointment Checker
Polls every CHECK_INTERVAL seconds and emails when a slot opens.

Usage:
    1. cp .env.example .env   # then fill in your email credentials
    2. pip install -r requirements.txt
    3. python main.py
"""

import os
import sys
import time
import logging
from datetime import datetime
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

    # Validate required env vars
    for var in ("EMAIL_FROM", "EMAIL_TO", "EMAIL_PASSWORD"):
        if not os.environ.get(var):
            log.error("Missing required env var: %s", var)
            sys.exit(1)

    interval = int(os.environ.get("CHECK_INTERVAL", "60"))
    log.info("KVR checker started — polling every %d seconds", interval)
    log.info("Booking URL: %s", checker.BOOKING_URL)

    while True:
        try:
            log.info("Fetching ALTCHA challenge...")
            token = altcha.get_captcha_token()
            log.info("ALTCHA solved, checking appointments...")

            available, dates = checker.check_appointments(token)

            if available:
                log.warning("*** APPOINTMENT(S) FOUND: %s ***", dates)
                try:
                    notifier.notify_appointment_found(dates)
                    log.info("Email notification sent.")
                except Exception as mail_err:
                    log.error("Failed to send email: %s", mail_err)
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
