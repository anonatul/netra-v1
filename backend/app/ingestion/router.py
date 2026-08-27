"""Ingestion — POST /api/v1/events.

Validation + idempotency (NFR-010) + immutable RAW storage.
The processing pipeline (extraction → clustering → priority) runs off this,
wired in app/pipeline.

Connectivity-aware (NFR-017): under CELLULAR_UNAVAILABLE only SMS uplinks
are accepted — ERSS/WHATSAPP/etc. are rejected with UPLINK_UNAVAILABLE and
audited, so the "network cut" demo is a real behavioral change, not a badge.
"""
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.database import get_db
from app.fusion.service import process_event
from app.models import AuditLog, Disaster, Event, Evidence, User
from app.queue.service import enqueue
from app.schemas import EventIn, EventOut
from app.security.rate import limit

router = APIRouter()

# Uplinks that survive a total cellular outage (signaling channel / satellite SMS).
SMS_UPLINKS = {"SMS"}


def _connectivity_mode(db: Session) -> str:
    disaster = db.query(Disaster).order_by(Disaster.id.desc()).first()
    return disaster.operating_mode if disaster else "NORMAL"


@router.post("/events", response_model=EventOut, status_code=status.HTTP_201_CREATED)
@limit("120/minute")
def create_event(
    request: Request,
    body: EventIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EventOut:
    mode = _connectivity_mode(db)

    if mode == "CELLULAR_UNAVAILABLE" and body.source_type not in SMS_UPLINKS:
        db.add(AuditLog(
            user_id=user.id,
            action="EVENT_REJECTED",
            target_type="EVENT",
            target_id=body.idempotency_key or f"{body.source_identifier or '?'}-{body.source_timestamp.isoformat()}",
            new_value={"source": body.source_type, "mode": mode},
            reason="uplink unavailable — only SMS accepted",
        ))
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "UPLINK_UNAVAILABLE", "message": f"Cellular uplink unavailable — {body.source_type} rejected; only SMS is getting through."},
        )

    if body.idempotency_key:
        existing = db.query(Event).filter(Event.idempotency_key == body.idempotency_key).first()
        if existing:
            return EventOut(event_id=existing.event_id, status=existing.processing_status)

    if mode in ("DEGRADED", "SEVERELY_DEGRADED"):
        # Real throughput consequence of a congested network, not a badge.
        time.sleep(0.3 if mode == "DEGRADED" else 0.8)

    event = Event(
        source_type=body.source_type,
        source_timestamp=body.source_timestamp,
        text=body.text,
        source_identifier=body.source_identifier,
        location_lat=body.location.lat if body.location else None,
        location_lon=body.location.lon if body.location else None,
        location_accuracy_m=body.location.accuracy_m if body.location else None,
        location_source="USER_SUPPLIED" if body.location else None,
        meta=body.metadata,
        idempotency_key=body.idempotency_key,
        processing_status="RECEIVED",
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    incident = process_event(db, event)
    db.add(AuditLog(
        user_id=user.id,
        action="EVENT_INGESTED",
        target_type="EVENT",
        target_id=event.event_id,
        new_value={"source": event.source_type, "incident_id": incident.incident_id if incident else None},
    ))
    db.commit()
    if event.text:
        enqueue(db, "LLM_ENRICH", event.event_id)
    return EventOut(event_id=event.event_id, status=event.processing_status, incident_id=incident.incident_id if incident else None)


@router.get("/events/recent")
def recent_events(limit: int = 30, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> list[dict]:
    """Most recent incoming reports — powers the live signal stream on the dashboard."""
    rows = (
        db.query(Event, Evidence.incident_id)
        .outerjoin(Evidence, Evidence.event_id == Event.event_id)
        .order_by(Event.source_timestamp.desc())
        .limit(min(max(limit, 1), 200))
        .all()
    )
    return [
        {
            "event_id": ev.event_id,
            "source_type": ev.source_type,
            "source_identifier": ev.source_identifier,
            "timestamp": ev.source_timestamp.isoformat(),
            "text": ev.text,
            "flagged": (ev.meta or {}).get("flagged"),
            "incident_id": incident_id,
            "status": ev.processing_status,
        }
        for ev, incident_id in rows
    ]


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> EventOut:
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Event not found"})
    return EventOut(event_id=event.event_id, status=event.processing_status)