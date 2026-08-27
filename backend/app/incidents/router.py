"""Incidents read API — list/detail + evidence timeline (traceability, docs/KB-TRACEABILITY.md)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.models import Evidence, Event, Incident, User

router = APIRouter()


@router.get("/incidents")
def list_incidents(
    priority: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    q = db.query(Incident)
    if priority:
        q = q.filter(Incident.priority == priority)
    if status:
        q = q.filter(Incident.status == status)
    return [_incident_out(i) for i in q.order_by(Incident.priority, Incident.updated_at.desc()).limit(limit).offset(offset)]


@router.get("/incidents/{incident_id}")
def get_incident(incident_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Incident not found"})
    return _incident_out(incident)


@router.get("/incidents/{incident_id}/evidence")
def incident_evidence(incident_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    """Full evidence timeline for an incident — what sources say, derived how, by which layer."""
    if db.query(Incident).filter(Incident.incident_id == incident_id).first() is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Incident not found"})
    rows = (
        db.query(Evidence, Event)
        .join(Event, Event.event_id == Evidence.event_id)
        .filter(Evidence.incident_id == incident_id)
        .order_by(Evidence.timestamp.asc())
        .all()
    )
    return [
        {
            "event_id": e.event_id,
            "source_type": e.source_type,
            "source_identifier": ev.source_identifier,
            "timestamp": e.timestamp.isoformat(),
            "text": ev.text,
            "flagged": (ev.meta or {}).get("flagged"),
            "extraction": e.extraction,
            "confidence": e.confidence,
            "relationship": e.relationship,
        }
        for e, ev in rows
    ]


def _incident_out(i: Incident) -> dict:
    return {
        "incident_id": i.incident_id,
        "status": i.status,
        "priority": i.priority,
        "severity": i.severity,
        "confidence": i.confidence,
        "location": {"lat": i.location_lat, "lon": i.location_lon, "confidence": i.location_confidence},
        "victim_estimate": i.victim_estimate,
        "vulnerability": i.vulnerability,
        "evidence_count": i.evidence_count,
        "independent_source_count": i.independent_source_count,
        "zone_id": i.zone_id,
        "created_at": i.created_at,
        "updated_at": i.updated_at,
        "last_evidence_at": i.last_evidence_at,
        "resolved_at": i.resolved_at,
    }