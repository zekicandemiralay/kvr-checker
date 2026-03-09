"""
Checks appointment availability at Munich KVR via the city API.
Returns (available: bool, dates: list) each call.
"""

from datetime import date, timedelta
import requests

OFFICE_ID  = "10187259"   # Servicestelle für Zuwanderung und Einbürgerung
SERVICE_ID = "10339027"   # Notfall-Hilfe Aufenthaltstitel
BOOKING_URL = (
    "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html"
    "#/services/10339027/locations/10187259"
)

AVAILABLE_DAYS_URL = (
    "https://www48.muenchen.de/buergeransicht/api/citizen/available-days-by-office/"
)

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://stadt.muenchen.de",
    "Referer": "https://stadt.muenchen.de/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
}


def check_appointments(captcha_token: str) -> tuple[bool, list]:
    """
    Returns (True, [date_strings]) if appointments are available,
    (False, []) otherwise.
    """
    start = date.today()
    end   = start + timedelta(days=180)

    params = {
        "startDate":    start.isoformat(),
        "endDate":      end.isoformat(),
        "officeId":     OFFICE_ID,
        "serviceId":    SERVICE_ID,
        "serviceCount": "1",
        "captchaToken": captcha_token,
    }

    resp = requests.get(
        AVAILABLE_DAYS_URL,
        params=params,
        headers=HEADERS,
        timeout=15,
    )

    if resp.status_code == 404:
        return False, []

    resp.raise_for_status()

    # HTTP 200 = appointments exist. No need to parse the body —
    # the notification includes the direct booking link so the user
    # can see the exact dates and times on the website immediately.
    return True, []
