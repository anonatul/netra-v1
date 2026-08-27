"""Field updates API — HUMAN verification flow (docs/API.md)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_role
from app.database import get_db
from app.lifecycle.service import apply_field_update
from app.models import FieldUpdate, Incident, User
from app.schemas import FieldUpdateIn

router = APIRouter()


@router.post("/incidents/{incident_id}/field-updates")
def create_field_update(
    incident_id: str,
    body: FieldUpdateIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("FIELD_RESPONDER", "OPERATOR", "COMMANDER", "ADMIN")),
) -> dict:
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Incident not found"})
    try:
        return apply_field_update(db, incident, body.update_type, body.values, body.notes, user)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"code": "VALIDATION_ERROR", "message": str(exc)})


@router.get("/incidents/{incident_id}/field-updates")
def list_field_updates(
    incident_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[dict]:
    if db.query(Incident).filter(Incident.incident_id == incident_id).first() is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Incident not found"})
    updates = (
        db.query(FieldUpdate)
        .filter(FieldUpdate.incident_id == incident_id)
        .order_by(FieldUpdate.timestamp.desc())
        .all()
    )
    return [
        {
            "update_type": u.update_type,
            "values": u.values,
            "notes": u.notes,
            "user_id": u.user_id,
            "timestamp": u.timestamp,
            "sync_state": u.sync_state,
        }
        for u in updates
    ]