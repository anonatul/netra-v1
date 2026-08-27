"""Lifecycle + recommendations integration tests."""
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://netra:netra@localhost:5433/netra_test"
)
from app.database import Base  # noqa: E402
from app.lifecycle.service import apply_field_update  # noqa: E402
from app.models import Incident, Recommendation, User  # noqa: E402
from app.recommend.service import suggest  # noqa: E402

engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _user(db):
    u = User(username="field-1", password_hash="x", role="FIELD_RESPONDER", display_name="Field One")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _incident(db, **kw):
    defaults = {
        "status": "NEW",
        "location_lat": 19.0760,
        "location_lon": 72.8777,
        "location_accuracy_m": 50,
        "location_confidence": 0.8,
        "severity": "HIGH",
        "vulnerability": {"water_rising": True, "elderly": True},
        "victim_estimate": 5,
        "evidence_count": 2,
        "independent_source_count": 2,
        "confidence": 0.7,
        "priority": "P1",
        "last_evidence_at": datetime.now(timezone.utc),
    }
    defaults.update(kw)
    inc = Incident(**defaults)
    db.add(inc)
    db.commit()
    db.refresh(inc)
    return inc


def test_suggest_boats_for_flood(db):
    inc = _incident(db)
    r = suggest(db, inc)
    assert any(res["resource"] == "RESCUE_BOATS" for res in r["resources"])
    assert any(res["resource"] == "MEDICAL_TEAM" for res in r["resources"])
    assert r["rule_version"] == "recommend-v1"


def test_rescued_leaves_active_flow(db):
    inc = _incident(db)
    user = _user(db)
    result = apply_field_update(db, inc, "RESCUED", {}, "crew reached, everyone safe", user)
    assert inc.status == "RESCUED"
    assert inc.resolved_at is not None
    assert result["status"] == "RESCUED"


def test_false_positive_flag(db):
    inc = _incident(db)
    user = _user(db)
    apply_field_update(db, inc, "FALSE", {}, "prank call", user)
    assert inc.status == "FALSE"


def test_verify_boosts_confidence(db):
    inc = _incident(db, confidence=0.6, location_confidence=0.7)
    user = _user(db)
    apply_field_update(db, inc, "VERIFY", {}, "team on site, confirmed", user)
    assert inc.confidence >= 0.7
    assert inc.location_confidence >= 0.8


def test_victim_count_update(db):
    inc = _incident(db)
    user = _user(db)
    apply_field_update(db, inc, "VICTIM_COUNT", {"count": 12}, "counted on site", user)
    assert inc.victim_estimate == 12


def test_recommendation_superseded_on_new_evidence(db):
    inc = _incident(db)
    suggest(db, inc)
    user = _user(db)
    apply_field_update(db, inc, "MEDICAL", {"critical": True}, "bleeding confirmed", user)
    pending = (
        db.query(Recommendation)
        .filter(Recommendation.incident_id == inc.incident_id, Recommendation.status == "SUGGESTED")
        .count()
    )
    assert pending == 1
    superseded = db.query(Recommendation).filter(Recommendation.status == "SUPERSEDED").count()
    assert superseded >= 1