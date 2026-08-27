"""Security tests: RBAC, audit trail, rate limiting (SECURITY.md)."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _token(role: str) -> str:
    creds = {"commander": ("commander", "commander123"), "operator": ("operator", "operator123"),
             "auditor": ("auditor", "auditor123"), "admin": ("admin", "admin123")}
    u, p = creds[role]
    r = client.post("/api/v1/auth/login", json={"username": u, "password": p})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(role: str) -> dict:
    return {"Authorization": f"Bearer {_token(role)}"}


def test_login_wrong_password_401():
    r = client.post("/api/v1/auth/login", json={"username": "commander", "password": "wrong"})
    assert r.status_code == 401


def test_events_require_auth():
    r = client.post("/api/v1/events", json={})
    assert r.status_code == 401


def test_audit_requires_auditor_or_admin():
    r = client.get("/api/v1/audit", headers=_auth("operator"))
    assert r.status_code == 403
    r = client.get("/api/v1/audit", headers=_auth("auditor"))
    assert r.status_code == 200
    assert "entries" in r.json()


def test_audit_trail_records_actions():
    h = _auth("commander")
    r = client.post("/api/v1/events", headers=h, json={
        "source_type": "SMS", "source_timestamp": "2026-08-01T10:00:00Z",
        "text": "building collapse at bandra east, 2 people trapped",
        "source_identifier": "audit-test-1", "location": {"lat": 19.06, "lon": 72.84},
    })
    assert r.status_code == 201
    r = client.get("/api/v1/audit", headers=_auth("auditor"))
    assert r.status_code == 200
    assert len(r.json()["entries"]) > 0


def test_rate_limit_events():
    h = _auth("operator")
    for _ in range(130):
        client.post("/api/v1/events", headers=h, json={
            "source_type": "SMS", "source_timestamp": "2026-08-01T10:00:00Z",
            "text": "flooding", "source_identifier": "rl-test", "location": {"lat": 19.06, "lon": 72.84},
        })
    r = client.post("/api/v1/events", headers=h, json={
        "source_type": "SMS", "source_timestamp": "2026-08-01T10:00:00Z",
        "text": "flooding", "source_identifier": "rl-test-last", "location": {"lat": 19.06, "lon": 72.84},
    })
    assert r.status_code == 429


def test_rate_limit_login():
    # runs last: floods the login bucket; a fresh client login must then be throttled
    for _ in range(25):
        client.post("/api/v1/auth/login", json={"username": "x", "password": "y"})
    r = client.post("/api/v1/auth/login", json={"username": "commander", "password": "commander123"})
    assert r.status_code == 429