# tests/conftest.py
import os
import pytest
from utils.http import get_client

# Controls (override in CI or locally if needed)
API_BASE = os.getenv("API_BASE", "https://reqres.in")
API_SKIP_ON_403 = os.getenv("API_SKIP_ON_403", "1")  # "1"=skip session on 403/5xx, "0"=don't skip
API_STRICT = os.getenv("API_STRICT", "0")            # "1"=xfail on 403/5xx instead of skip

@pytest.fixture(scope="session")
def api_base():
    return API_BASE

@pytest.fixture(scope="session", autouse=True)
def probe_public_api():
    s = get_client()
    url = f"{API_BASE}/api/users"
    try:
        r = s.get(url, params={"page": 1}, timeout=10)
    except Exception as e:
        if API_STRICT == "1":
            pytest.xfail(f"Cannot reach {API_BASE}: {e}")
        else:
            pytest.skip(f"Cannot reach {API_BASE}: {e}")

    if r.status_code in (403, 429) or r.status_code >= 500:
        msg = f"{API_BASE} blocked/unstable (HTTP {r.status_code})."
        if API_SKIP_ON_403 == "1" and API_STRICT != "1":
            pytest.skip(msg)
        else:
            pytest.xfail(msg)

@pytest.fixture(scope="session")
def api(api_base):
    return {"base": api_base, "s": get_client()}
