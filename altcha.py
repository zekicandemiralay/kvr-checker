"""
ALTCHA proof-of-work solver.

Flow:
  1. GET /captcha-challenge/  -> {algorithm, challenge, maxnumber, salt, signature}
  2. Find n in [0, maxnumber] where SHA-256(salt + "$" + n) == challenge
  3. POST /captcha-verify/    -> JWT captchaToken
"""

import base64
import hashlib
import json
import requests

CHALLENGE_URL = "https://www48.muenchen.de/buergeransicht/api/citizen/captcha-challenge/"
VERIFY_URL    = "https://www48.muenchen.de/buergeransicht/api/citizen/captcha-verify/"

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


def get_challenge() -> dict:
    resp = requests.get(CHALLENGE_URL, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def solve_challenge(data: dict) -> int:
    """Brute-force find the nonce that matches the challenge hash."""
    salt = data["salt"]
    challenge = data["challenge"].lower()
    maxnumber = data["maxnumber"]

    for n in range(maxnumber + 1):
        digest = hashlib.sha256(f"{salt}{n}".encode()).hexdigest()
        if digest == challenge:
            return n

    raise ValueError(f"Could not solve ALTCHA challenge within maxnumber={maxnumber}")


def get_captcha_token() -> str:
    """Full ALTCHA flow: fetch challenge → solve → verify → return JWT."""
    data = get_challenge()
    n = solve_challenge(data)

    payload_obj = {
        "algorithm": data["algorithm"],
        "challenge": data["challenge"],
        "number": n,
        "salt": data["salt"],
        "signature": data["signature"],
        "test": False,
        "took": 0,
    }
    payload_b64 = base64.b64encode(json.dumps(payload_obj).encode()).decode()

    headers = {**HEADERS, "Content-Type": "application/json"}
    resp = requests.post(
        VERIFY_URL,
        json={"payload": payload_b64},
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()

    body = resp.json()
    # Response is {"token": "<JWT>"} or the token string directly
    if isinstance(body, dict):
        token = body.get("token") or body.get("captchaToken") or body.get("data")
    else:
        token = body

    if not token:
        raise ValueError(f"Unexpected captcha-verify response: {body}")

    return token
