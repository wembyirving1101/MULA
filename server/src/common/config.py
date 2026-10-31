import math
import os
from urllib.parse import urlsplit


HERMES_BASE_URL = os.getenv("HERMES_BASE_URL", "http://127.0.0.1:8642").rstrip("/")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "").strip()
HERMES_MODEL = os.getenv("HERMES_MODEL", "hermes-agent").strip()
HERMES_TIMEOUT_SECONDS = float(os.getenv("HERMES_TIMEOUT_SECONDS", "120"))

url = urlsplit(HERMES_BASE_URL)
if (
    url.scheme not in {"http", "https"}
    or not url.hostname
    or url.username
    or url.password
    or url.query
    or url.fragment
):
    raise ValueError("HERMES_BASE_URL must be an HTTP(S) URL without credentials or query parameters.")
if not HERMES_MODEL:
    raise ValueError("HERMES_MODEL must not be empty.")
if not math.isfinite(HERMES_TIMEOUT_SECONDS) or HERMES_TIMEOUT_SECONDS <= 0:
    raise ValueError("HERMES_TIMEOUT_SECONDS must be a positive finite number.")
