"""System status — connectivity state + source health (NFR-017/099)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.llm.gateway import LLM_STATE
from app.models import Disaster, Event, Incident, OperationalZone, User

router = APIRouter()


@router.get("/system/status")
def system_status(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    disaster = db.query(Disaster).order_by(Disaster.id.desc()).first()
    event_counts = dict(db.query(Event.source_type, func.count(Event.id)).group_by(Event.source_type).all())
    return {
        "connectivity_mode": disaster.operating_mode if disaster else "NORMAL",
        "disaster_active": disaster.disaster_id if disaster else None,
        "events_by_source": event_counts,
        "total_events": sum(event_counts.values()),
        "total_incidents": db.query(Incident).count(),
        "open_incidents": db.query(Incident).filter(Incident.status.notin_(["RESCUED", "FALSE"])).count(),
        "llm_health": "HEALTHY" if LLM_STATE.get("healthy") else ("DEGRADED" if LLM_STATE.get("healthy") is False else "UNKNOWN"),
        "llm_last_check": LLM_STATE.get("last_check"),
        "llm_last_error": LLM_STATE.get("last_error"),
        "llm_last_latency_ms": LLM_STATE.get("last_latency_ms"),
    }


@router.get("/map-data")
def map_data(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    """Single fetch for the dashboard map: heat points, zones, incidents."""
    events = (
        db.query(Event)
        .filter(Event.location_lat.isnot(None), Event.processing_status != "RECEIVED")
        .order_by(Event.id.desc())
        .limit(2000)
        .all()
    )
    zones = db.query(OperationalZone).filter(OperationalZone.status == "ACTIVE").all()
    incidents = db.query(Incident).filter(Incident.status.notin_(["RESCUED", "FALSE"])).all()
    return {
        "heat_points": [
            {"lat": e.location_lat, "lon": e.location_lon, "weight": 1, "flagged": (e.meta or {}).get("flagged")}
            for e in events
        ],
        "zones": [
            {
                "zone_id": z.zone_id,
                "lat": z.center_lat,
                "lon": z.center_lon,
                "radius_m": z.radius_m,
                "priority": z.priority,
                "confidence": z.confidence,
                "incident_count": len(z.incident_ids or []),
                "evidence_count": z.evidence_count,
                "source_count": z.independent_source_count,
            }
            for z in zones
        ],
        "incidents": [
            {
                "incident_id": i.incident_id,
                "lat": i.location_lat,
                "lon": i.location_lon,
                "priority": i.priority,
                "severity": i.severity,
                "confidence": i.confidence,
                "vulnerability": i.vulnerability or {},
                "victim_estimate": i.victim_estimate,
                "evidence_count": i.evidence_count,
                "source_count": i.independent_source_count,
                "status": i.status,
                "updated_at": i.updated_at,
            }
            for i in incidents
        ],
    }