"""Fusion pipeline — golden path: event → incident → evidence → priority.

Rules are synchronous (critical path, always-on). LLM enrichment hooks in later
as async L3 (docs/AI.md fallback chain) without touching this determinism.
"""
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.clustering.service import recompute_zones
from app.extraction.rules import extract
from app.models import Event, Evidence, Incident
from app.priority.service import apply_priority
from app.recommend.service import suggest

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 0}
MATCH_WINDOW_HOURS = 6
MIN_MATCH_RADIUS_M = 50
MAX_MATCH_RADIUS_M = 1500


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    if None in (lat1, lon1, lat2, lon2):
        return float("inf")
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _location_confidence(accuracy_m: float | None) -> float:
    if accuracy_m is None:
        return 0.1
    if accuracy_m >= 1000:
        return 0.3
    if accuracy_m >= 200:
        return 0.5
    if accuracy_m >= 50:
        return 0.8
    return 0.95


def _match_radius_m(accuracy_m: float | None) -> float:
    base = max(MIN_MATCH_RADIUS_M, (accuracy_m or MIN_MATCH_RADIUS_M) * 2)
    return min(base, MAX_MATCH_RADIUS_M)


def _find_candidate(db: Session, lat: float | None, lon: float | None, ts: datetime) -> Incident | None:
    """Adaptive uncertainty-aware matching (AD-005): radius from location accuracy,
    capped; recency window; nearest incident wins."""
    if lat is None or lon is None:
        return None
    window = ts - timedelta(hours=MATCH_WINDOW_HOURS)
    candidates = (
        db.query(Incident)
        .filter(
            Incident.status.notin_(["RESCUED", "FALSE"]),
            Incident.last_evidence_at >= window,
            Incident.location_lat.isnot(None),
        )
        .all()
    )
    best: tuple[float, Incident] | None = None
    for inc in candidates:
        d = _haversine_m(lat, lon, inc.location_lat, inc.location_lon)
        if d <= _match_radius_m(inc.location_accuracy_m or None):
            if best is None or d < best[0]:
                best = (d, inc)
    return best[1] if best else None


def process_event(db: Session, event: Event) -> Incident | None:
    """Process one RAW event: extract → match/create incident → attach evidence → update."""
    text = event.text or ""
    extraction = extract(text) if text else {
        "severity": "UNKNOWN",
        "severity_hits": [],
        "disaster": "UNKNOWN",
        "safe": False,
        "fake": False,
        "victim_hint": None,
        "attributes": {},
        "model": "rules-v1",
        "confidence": 1.0,
    }
    attributes = extraction["attributes"]

    if extraction.get("safe") and not attributes:
        event.processing_status = "PROCESSED"
        event.meta = {**(event.meta or {}), "flagged": "SAFE"}
        db.commit()
        return None

    if extraction.get("fake"):
        event.processing_status = "PROCESSED"
        event.meta = {**(event.meta or {}), "flagged": "SUSPECTED_FAKE", "extraction": extraction}
        db.add(Evidence(
            event_id=event.event_id,
            source_type=event.source_type,
            timestamp=event.received_timestamp,
            content_reference=event.event_id,
            extraction=extraction,
            confidence=0.1,
            relationship="PRIMARY",
        ))
        db.commit()
        return None

    incident = _find_candidate(db, event.location_lat, event.location_lon, event.source_timestamp)
    if incident is None:
        incident = Incident(
            disaster_id=event.disaster_id,
            location_lat=event.location_lat,
            location_lon=event.location_lon,
            location_accuracy_m=event.location_accuracy_m,
            location_confidence=_location_confidence(event.location_accuracy_m),
            severity=extraction["severity"] if extraction["severity"] != "UNKNOWN" else "UNKNOWN",
            confidence=0.6,
            last_evidence_at=event.source_timestamp,
        )
        db.add(incident)
        db.flush()

    evidence = Evidence(
        event_id=event.event_id,
        incident_id=incident.incident_id,
        source_type=event.source_type,
        timestamp=event.received_timestamp,
        content_reference=event.event_id,
        location_lat=event.location_lat,
        location_lon=event.location_lon,
        location_accuracy_m=event.location_accuracy_m,
        extraction=extraction,
        confidence=extraction["confidence"],
        relationship="PRIMARY",
    )
    db.add(evidence)

    severity = extraction["severity"]
    if severity != "UNKNOWN" and SEVERITY_RANK[severity] > SEVERITY_RANK[incident.severity]:
        incident.severity = severity

    if extraction.get("victim_hint") and (incident.victim_estimate is None or extraction["victim_hint"] > incident.victim_estimate):
        incident.victim_estimate = extraction["victim_hint"]

    vuln = dict(incident.vulnerability or {})
    for key, spec in attributes.items():
        if key not in ("water_rising", "trapped", "access_issue") or key not in vuln:
            vuln[key] = True
    incident.vulnerability = vuln

    incident.evidence_count = (incident.evidence_count or 0) + 1
    if event.source_identifier:
        existing_sources = incident.meta.get("sources", []) if incident.meta else []
        if event.source_identifier not in existing_sources:
            existing_sources.append(event.source_identifier)
            incident.meta = {**(incident.meta or {}), "sources": existing_sources}
            incident.independent_source_count = len(existing_sources)
    incident.last_evidence_at = event.source_timestamp
    incident.updated_at = datetime.now(timezone.utc)

    incident.priority = apply_priority(db, incident, source="SYSTEM")["level"]
    incident.confidence = min(0.95, 0.6 + 0.05 * (incident.evidence_count - 1))

    event.processing_status = "PROCESSED"
    event.disaster_id = incident.disaster_id
    db.commit()
    suggest(db, incident, overwrite=False)
    recompute_zones(db)
    return incident