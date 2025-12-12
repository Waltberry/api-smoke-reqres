import time
import re
import pytest
from jsonschema import validate, Draft202012Validator
from utils.http import get_client

# ---------- Fixtures ----------

@pytest.fixture(scope="session")
def api():
    base_url, session = get_client()
    return {"base": base_url, "s": session}

# ---------- JSON Schemas (spot checks; intentionally minimal) ----------

USER_SCHEMA = {
    "type": "object",
    "required": ["data", "support"],
    "properties": {
        "data": {
            "type": "object",
            "required": ["id", "email", "first_name", "last_name", "avatar"],
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string", "pattern": r"@.+\..+"},
                "first_name": {"type": "string"},
                "last_name": {"type": "string"},
                "avatar": {"type": "string"}
            }
        },
        "support": {"type": "object"}
    }
}

CREATE_USER_SCHEMA = {
    "type": "object",
    "required": ["name", "job", "id", "createdAt"],
    "properties": {
        "name": {"type": "string"},
        "job": {"type": "string"},
        "id": {"type": ["string", "integer"]},
        "createdAt": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}T"}
    }
}

REGISTER_SUCCESS_SCHEMA = {
    "type": "object",
    "required": ["id", "token"],
    "properties": {
        "id": {"type": "integer"},
        "token": {"type": "string"}
    }
}

TOKEN_SCHEMA = {
    "type": "object",
    "required": ["token"],
    "properties": {"token": {"type": "string"}}
}

ERROR_SCHEMA = {
    "type": "object",
    "required": ["error"],
    "properties": {"error": {"type": "string"}}
}

# ---------- Tests ----------

@pytest.mark.smoke
def test_health_list_users(api):
    """Basic health: list users returns 200 and non-empty data."""
    r = api["s"].get(f'{api["base"]}/api/users', params={"page": 2}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert isinstance(body.get("data"), list) and len(body["data"]) > 0

@pytest.mark.smoke
@pytest.mark.schema
def test_get_user_schema(api):
    """GET /api/users/2 matches spot-check schema."""
    r = api["s"].get(f'{api["base"]}/api/users/2', timeout=15)
    assert r.status_code == 200
    body = r.json()
    validate(instance=body, schema=USER_SCHEMA, cls=Draft202012Validator)

@pytest.mark.negative
def test_get_user_not_found(api):
    """GET /api/users/23 -> 404"""
    r = api["s"].get(f'{api["base"]}/api/users/23', timeout=15)
    assert r.status_code == 404
    assert r.text.strip() in ("{}", "")  # reqres returns empty body for 404

@pytest.mark.smoke
@pytest.mark.schema
def test_create_user(api):
    """POST /api/users -> 201 + spot schema (id, createdAt, e.g.)."""
    payload = {"name": "morpheus", "job": "leader"}
    r = api["s"].post(f'{api["base"]}/api/users', json=payload, timeout=15)
    assert r.status_code == 201
    body = r.json()
    # augment schema expectations with echoed fields
    assert body.get("name") == "morpheus"
    assert body.get("job") == "leader"
    validate(instance=body, schema=CREATE_USER_SCHEMA, cls=Draft202012Validator)

@pytest.mark.auth
def test_login_success(api):
    """POST /api/login with correct creds -> token."""
    payload = {"email": "eve.holt@reqres.in", "password": "cityslicka"}
    r = api["s"].post(f'{api["base"]}/api/login', json=payload, timeout=15)
    assert r.status_code == 200
    validate(instance=r.json(), schema=TOKEN_SCHEMA, cls=Draft202012Validator)

@pytest.mark.auth
@pytest.mark.negative
def test_login_missing_password(api):
    """POST /api/login missing password -> 400 + error message."""
    payload = {"email": "peter@klaven"}
    r = api["s"].post(f'{api["base"]}/api/login', json=payload, timeout=15)
    assert r.status_code == 400
    body = r.json()
    validate(instance=body, schema=ERROR_SCHEMA, cls=Draft202012Validator)
    assert "password" in body["error"].lower()

@pytest.mark.auth
def test_register_success(api):
    """POST /api/register with supported email -> 200 + id + token."""
    payload = {"email": "eve.holt@reqres.in", "password": "pistol"}
    r = api["s"].post(f'{api["base"]}/api/register', json=payload, timeout=15)
    assert r.status_code == 200
    validate(instance=r.json(), schema=REGISTER_SUCCESS_SCHEMA, cls=Draft202012Validator)

@pytest.mark.negative
def test_register_missing_password(api):
    """POST /api/register missing password -> 400 + error."""
    payload = {"email": "sydney@fife"}
    r = api["s"].post(f'{api["base"]}/api/register', json=payload, timeout=15)
    assert r.status_code == 400
    validate(instance=r.json(), schema=ERROR_SCHEMA, cls=Draft202012Validator)

@pytest.mark.smoke
def test_soft_rate_limit_burst(api):
    """
    Soft check: quick burst should not 429 on a public demo.
    If it does, report clearly (don’t flake CI with random network failures).
    """
    statuses = []
    for _ in range(5):
        r = api["s"].get(f'{api["base"]}/api/users', params={"page": 1}, timeout=10)
        statuses.append(r.status_code)
        time.sleep(0.2)
    assert 429 not in statuses, f"Hit rate limit unexpectedly: {statuses}"
