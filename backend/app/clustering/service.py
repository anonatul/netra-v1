"""Adaptive uncertainty-aware clustering into operational zones (AD-005, docs/SCHEMA.md).

Deterministic greedy: incidents ordered by priority (P1 first), each seeds a zone
and absorbs neighbors within an adaptive radius derived from location accuracy
— never a fixed 50 m blanket. Zone center is confidence-weighted.
"""
import math

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Incident, OperationalZone

ZONE_MIN_RADIUS_M = 400.0
ZONE_MAX_RADIUS_M = 2000.0
ZONE_RADIUS_FACTOR = 2.0
ZONE_LOCK_KEY = 7301  # advisory lock: serializes zone recomputes (deadlock fix)

PRIORITY_RANK = {"P1": 3, "P2": 2, "P3": 1, "P4": 0, "UNRATED": -1}


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _adaptive_radius(accuracy_m: float | None) -> float:
    base = (accuracy_m or ZONE_MIN_RADIUS_M) * ZONE_RADIUS_FACTOR
    return min(max(base, ZONE_MIN_RADIUS_M), ZONE_MAX_RADIUS_M)


def _member_radius(acc: float | None, confidence: float | None) -> float:
    """Radius at which a member incident pulls the zone centroid (accuracy-aware)."""
    return _adaptive_radius(acc) * (0.5 + (confidence or 0.5))


def recompute_zones(db: Session) -> list[OperationalZone]:
    """Rebuild operational zones from all active incidents. Deterministic.

    Concurrent recomputes are serialized via a transaction-scoped advisory lock:
    without it, two recomputes (UPDATE incidents -> DELETE zones) deadlock.
    """
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": ZONE_LOCK_KEY})
    active = (
        db.query(Incident)
        .filter(Incident.status.notin_(["RESCUED", "FALSE"]), Incident.location_lat.isnot(None))
        .order_by(Incident.priority.desc(), Incident.updated_at.desc())
        .all()
    )

    db.query(Incident).update({Incident.zone_id: None})
    db.query(OperationalZone).delete()
    db.flush()

    zones: list[OperationalZone] = []
    assigned: set[str] = set()

    for inc in active:
        if inc.incident_id in assigned:
            continue
        inc_radius = _adaptive_radius(inc.location_accuracy_m)
        members = [inc]
        assigned.add(inc.incident_id)

        for other in active:
            if other.incident_id in assigned:
                continue
            d = _haversine_m(inc.location_lat, inc.location_lon, other.location_lat, other.location_lon)
            other_radius = _adaptive_radius(other.location_accuracy_m)
            if d <= (inc_radius + other_radius) / 2:
                members.append(other)
                assigned.add(other.incident_id)

        # confidence-weighted centroid
        total_w = 0.0
        lat = lon = 0.0
        max_radius = 0.0
        evidence = sources = 0
        max_priority = "P4"
        for m in members:
            w = (m.location_confidence or 0.5) * (1 + (m.evidence_count or 0))
            total_w += w
            lat += (m.location_lat or 0) * w
            lon += (m.location_lon or 0) * w
            max_radius = max(max_radius, _member_radius(m.location_accuracy_m, m.location_confidence))
            evidence += m.evidence_count or 0
            sources += m.independent_source_count or 0
            if PRIORITY_RANK.get(m.priority, -1) > PRIORITY_RANK.get(max_priority, -1):
                max_priority = m.priority
        lat /= total_w if total_w else 1
        lon /= total_w if total_w else 1

        zone = OperationalZone(
            center_lat=lat,
            center_lon=lon,
            radius_m=max(max_radius, ZONE_MIN_RADIUS_M),
            incident_ids=[m.incident_id for m in members],
            evidence_count=evidence,
            independent_source_count=sources,
            confidence=round(sum((m.confidence or 0.5) for m in members) / len(members), 3),
            priority=max_priority,
            status="ACTIVE",
        )
        db.add(zone)
        zones.append(zone)

    db.flush()
    for zone in zones:
        for inc_id in zone.incident_ids:
            inc = next((m for m in active if m.incident_id == inc_id), None)
            if inc:
                inc.zone_id = zone.zone_id
    db.commit()
    return zones