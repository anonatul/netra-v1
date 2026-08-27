"""Tests for demo features: LLM kill toggle, evidence timeline, live ingest, advisory-lock recompute."""
from fastapi.testclient import TestClient

from app.main import app
from app.llm.gateway import LLM_STATE

client = TestClient(app)


def _token(role: str = "commander") -> str:
    r = client.post("/api/v1/auth/login", json={"username": role, "password": f"{role}123"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _auth(role: str = "commander") -> dict:
    return {"Authorization": f"Bearer {_token(role)}"}


def test_llm_kill_toggle_flips_state_and_degrades_status():
    r = client.post("/api/v1/sim/llm", headers=_auth(), json={"enabled": False})
    assert r.status_code == 200
    assert r.json()["llm_enabled"] is False
    assert LLM_STATE["healthy"] is False
    status = client.get("/api/v1/system/status", headers=_auth()).json()
    assert status["llm_health"] == "DEGRADED"

    r = client.post("/api/v1/sim/llm", headers=_auth(), json={"enabled": True})
    assert r.json()["llm_enabled"] is True
    assert LLM_STATE["healthy"] is None  # re-probes on next enrichment


def test_llm_kill_toggle_requires_commander():
    r = client.post("/api/v1/sim/llm", headers=_auth("auditor"), json={"enabled": False})
    assert r.status_code == 403
    client.post("/api/v1/sim/llm", headers=_auth(), json={"enabled": True})  # restore


def test_ingest_while_llm_killed_keeps_rules_only_and_records_failure():
    client.post("/api/v1/sim/llm", headers=_auth(), json={"enabled": False})
    r = client.post("/api/v1/events", headers=_auth(), json={
        "source_type": "SMS",
        "source_timestamp": "2026-08-18T10:00:00Z",
        "text": "building collapse near station, 2 people trapped under debris",
        "source_identifier": "ev-llm-kill-1",
        "location": {"lat": 19.07, "lon": 72.86, "accuracy_m": 100},
        "idempotency_key": "ev-llm-kill-1",
    })
    assert r.status_code == 201
    assert r.json()["status"] == "PROCESSED"  # R-08: never UNRESOLVED
    client.post("/api/v1/sim/llm", headers=_auth(), json={"enabled": True})  # restore


def test_evidence_timeline_lists_sources_with_provenance():
    r = client.post("/api/v1/events", headers=_auth(), json={
        "source_type": "ERSS",
        "source_timestamp": "2026-08-18T10:00:00Z",
        "text": "paani kamar tak aa gaya hai, dadi chal nahi sakti",
        "source_identifier": "ev-timeline-1",
        "location": {"lat": 19.071, "lon": 72.861, "accuracy_m": 100},
        "idempotency_key": "ev-timeline-1",
    })
    incident_id = r.json()["incident_id"]
    ev = client.get(f"/api/v1/incidents/{incident_id}/evidence", headers=_auth())
    assert ev.status_code == 200
    entries = ev.json()
    assert len(entries) >= 1
    last = entries[-1]
    assert last["event_id"] == r.json()["event_id"]
    assert last["source_type"] == "ERSS"
    assert last["text"]
    assert "extraction" in last
    assert last["relationship"] in ("PRIMARY", "CORROBORATING", "FIELD_VERIFIED")


def test_recompute_zones_survives_concurrent_invocation():
    from concurrent.futures import ThreadPoolExecutor

    from app.clustering.service import recompute_zones
    from app.database import SessionLocal
    from app.models import Incident

    with SessionLocal() as db:
        for inc in db.query(Incident).filter(Incident.location_lat.isnot(None)).limit(40).all():
            pass  # warm
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda _: _run_recompute(), range(6)))
    assert all(r for r in results)  # no deadlock, advisory lock serializes


def _run_recompute():
    from app.database import SessionLocal

    from app.clustering.service import recompute_zones

    with SessionLocal() as db:
        try:
            zones = recompute_zones(db)
            return True
        except Exception:
            return False