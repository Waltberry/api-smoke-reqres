import os
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

DEFAULT_BASE_URL = os.getenv("BASE_URL", "https://reqres.in")

def _retrying_session(total=3, backoff=0.5):
    """
    Create a requests.Session with idempotent-safe retries.
    """
    s = requests.Session()
    retry = Retry(
        total=total,
        read=total,
        connect=total,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({"Accept": "application/json"})
    return s

def get_client():
    """
    Returns (base_url, requests.Session) with retries.
    """
    return DEFAULT_BASE_URL.rstrip("/"), _retrying_session()
