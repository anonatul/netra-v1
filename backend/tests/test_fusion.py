"""Fusion pipeline integration tests — golden path on a dedicated test DB."""
import os
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://netra:netra@localhost:5433/netra_test"
)
from app.database import Base  # noqa: E402
from app.fusion.service import process_event  # noqa: E402
from app.models import Event, Incident  # noqa: E402

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


def _event(session, text, lat, lon, acc, device, ts=None):
    e = Event(
        source_type="SMS",
        source_timestamp=ts or datetime.now(timezone.utc),
        text=text,
        source_identifier=device,
        location_lat=lat,
        location_lon=lon,
        location_accuracy_m=acc,
    )
    session.add(e)
    session.commit()
    session.refresh(e)
    return e


def test_two_reports_same_incident(db):
    e1 = _event(db, "Paani kamar tak aa gaya hai, dadi chhat par phans gaye", 19.0760, 72.8777, 50, "dev-a")
    inc1 = process_event(db, e1)
    assert inc1 is not None

    e2 = _event(db, "Water rising fast, trapped on rooftop, grandmother cannot walk", 19.0762, 72.8780, 100, "dev-b")
    inc2 = process_event(db, e2)
    assert inc2 is not None
    assert inc1.incident_id == inc2.incident_id
    db.refresh(inc1)
    assert inc1.evidence_count == 2
    assert inc1.independent_source_count == 2
    assert inc1.vulnerability.get("elderly")


def test_far_report_separate_incident(db):
    e1 = _event(db, "Paani chhat par phans gaye", 19.0760, 72.8777, 50, "dev-a")
    inc1 = process_event(db, e1)
    e2 = _event(db, "Building collapsed, people stuck inside", 19.2400, 72.8550, 200, "dev-b")
    inc2 = process_event(db, e2)
    assert inc1.incident_id != inc2.incident_id


def test_duplicate_device_single_source(db):
    e1 = _event(db, "paani badh raha hai, phans gaye", 19.0760, 72.8777, 50, "dev-a")
    inc1 = process_event(db, e1)
    e2 = _event(db, "paani aur badh gaya", 19.0761, 72.8778, 50, "dev-a")
    inc2 = process_event(db, e2)
    assert inc1.incident_id == inc2.incident_id
    db.refresh(inc1)
    assert inc1.evidence_count == 2
    assert inc1.independent_source_count == 1


def test_safe_message_no_incident(db):
    e = _event(db, "we are safe now, reached shelter", 19.0760, 72.8777, 50, "dev-a")
    assert process_event(db, e) is None
    assert e.processing_status == "PROCESSED"


def test_stale_report_not_merged(db):
    old = datetime.now(timezone.utc) - timedelta(hours=12)
    e1 = _event(db, "paani phans gaye", 19.0760, 72.8777, 50, "dev-a", ts=old)
    inc1 = process_event(db, e1)
    assert inc1 is not None
    e2 = _event(db, "paani phans gaye", 19.0761, 72.8778, 50, "dev-b")
    inc2 = process_event(db, e2)
    assert inc1.incident_id != inc2.incident_id