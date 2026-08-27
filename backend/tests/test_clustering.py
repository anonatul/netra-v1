"""Clustering tests — adaptive zones, priority ordering, uncertainty radius."""
import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://netra:netra@localhost:5433/netra_test"
)
from app.database import Base  # noqa: E402
from app.clustering.service import recompute_zones  # noqa: E402
from app.models import Incident, OperationalZone  # noqa: E402

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


def _incident(session, lat, lon, acc, priority="P3", confidence=0.8, evidence=1, sources=1, vuln=None):
    inc = Incident(
        status="NEW",
        location_lat=lat,
        location_lon=lon,
        location_accuracy_m=acc,
        location_confidence=confidence,
        severity="MEDIUM",
        confidence=confidence,
        priority=priority,
        vulnerability=vuln,
        evidence_count=evidence,
        independent_source_count=sources,
        last_evidence_at=datetime.now(timezone.utc),
    )
    session.add(inc)
    session.commit()
    session.refresh(inc)
    return inc


def test_nearby_incidents_single_zone(db):
    a = _incident(db, 19.0760, 72.8777, 50)
    b = _incident(db, 19.0763, 72.8780, 50)  # ~35m apart
    zones = recompute_zones(db)
    assert len(zones) == 1
    assert set(zones[0].incident_ids) == {a.incident_id, b.incident_id}
    assert zones[0].evidence_count == 2
    assert zones[0].independent_source_count == 2


def test_far_incidents_separate_zones(db):
    _incident(db, 19.0760, 72.8777, 50)
    _incident(db, 19.2400, 72.8550, 50)  # ~18km
    zones = recompute_zones(db)
    assert len(zones) == 2


def test_zone_priority_takes_max_member(db):
    _incident(db, 19.0760, 72.8777, 50, priority="P1")
    _incident(db, 19.0763, 72.8780, 50, priority="P3")
    zones = recompute_zones(db)
    assert zones[0].priority == "P1"


def test_uncertain_location_wider_radius(db):
    # high accuracy 50m → ~150m min radius; coarse 2km accuracy → 2km cap radius
    _incident(db, 19.0760, 72.8777, 50)
    _incident(db, 19.0800, 72.8800, 150)  # ~480m apart
    zones = recompute_zones(db)
    assert len(zones) == 2  # precise reports stay separate

    db.query(Incident).delete()
    db.commit()
    _incident(db, 19.0760, 72.8777, 2000)
    _incident(db, 19.0800, 72.8800, 2000)  # ~480m apart, both fuzzy
    zones = recompute_zones(db)
    assert len(zones) == 1  # fuzzy reports merge


def test_rescued_incidents_excluded(db):
    a = _incident(db, 19.0760, 72.8777, 50)
    b = _incident(db, 19.0763, 72.8780, 50)
    b.status = "RESCUED"
    db.commit()
    zones = recompute_zones(db)
    assert len(zones) == 1
    assert zones[0].incident_ids == [a.incident_id]