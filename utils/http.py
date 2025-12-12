# utils/http.py
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_TIMEOUT = int(os.getenv("API_TIMEOUT", "15"))

class TimeoutHTTPAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self._timeout = DEFAULT_TIMEOUT
        super().__init__(*args, **kwargs)
    def send(self, request, **kwargs):
        kwargs.setdefault("timeout", self._timeout)
        return super().send(request, **kwargs)

def get_client() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": os.getenv(
            "API_UA",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36 api-smoke/1.0"
        ),
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "close",
    })
    retry = Retry(
        total=3, connect=3, read=3,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST", "PUT", "DELETE", "PATCH"],
        raise_on_status=False,
    )
    adapter = TimeoutHTTPAdapter(max_retries=retry)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s
