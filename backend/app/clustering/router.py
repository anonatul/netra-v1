"""Operational zones API (docs/API.md)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.clustering.service import recompute_zones
from app.database import get_db
from app.models import Incident, OperationalZone, User

router = APIRouter()


@router.get("/zones")
def list_zones(
    priority: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    q = db.query(OperationalZone).filter(OperationalZone.status == "ACTIVE")
    if priority:
        q = q.filter(OperationalZone.priority == priority)
    zones = q.order_by(OperationalZone.priority.desc(), OperationalZone.updated_at.desc()).all()
    return [_zone_out(db, z) for z in zones]


@router.post("/zones/recompute")
def recompute(db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    zones = recompute_zones(db)
    return {"zones": len(zones), "message": "operational zones rebuilt"}


@router.get("/zones/{zone_id}")
def get_zone(zone_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    zone = db.query(OperationalZone).filter(OperationalZone.zone_id == zone_id).first()
    if zone is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Zone not found"})
    return _zone_out(db, zone)


def _zone_out(db: Session, zone: OperationalZone) -> dict:
    incidents = db.query(Incident).filter(Incident.incident_id.in_(zone.incident_ids or [])).all()
    return {
        "zone_id": zone.zone_id,
        "center": {"lat": zone.center_lat, "lon": zone.center_lon},
        "radius_m": zone.radius_m,
        "priority": zone.priority,
        "confidence": zone.confidence,
        "evidence_count": zone.evidence_count,
        "independent_source_count": zone.independent_source_count,
        "incident_ids": zone.incident_ids,
        "incidents": [
            {
                "incident_id": i.incident_id,
                "priority": i.priority,
                "severity": i.severity,
                "vulnerability": i.vulnerability,
                "victim_estimate": i.victim_estimate,
                "evidence_count": i.evidence_count,
                "independent_source_count": i.independent_source_count,
                "updated_at": i.updated_at,
            }
            for i in incidents
        ],
    }