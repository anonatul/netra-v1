"""Priority API — explainable score + audited human override (docs/PRIORITY.md)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_role
from app.database import get_db
from app.models import AuditLog, Incident, PriorityScore, User
from app.priority.service import apply_priority, compute_score
from app.schemas import PriorityOverrideIn

router = APIRouter()


@router.get("/incidents/{incident_id}/priority")
def get_priority(incident_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    incident = _get_or_404(db, incident_id)
    result = compute_score(incident)
    result["current_level"] = incident.priority
    history = (
        db.query(PriorityScore)
        .filter(PriorityScore.incident_id == incident_id)
        .order_by(PriorityScore.timestamp.desc())
        .limit(10)
        .all()
    )
    result["history"] = [
        {"score": h.score, "level": h.level, "rule_version": h.rule_version, "timestamp": h.timestamp} for h in history
    ]
    return result


@router.post("/incidents/{incident_id}/priority/override")
def override_priority(
    incident_id: str,
    body: PriorityOverrideIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("COMMANDER", "ADMIN")),
) -> dict:
    incident = _get_or_404(db, incident_id)
    previous = incident.priority
    incident.priority = body.priority
    db.add(PriorityScore(
        incident_id=incident.incident_id,
        score=compute_score(incident)["score"],
        level=body.priority,
        reasons={"override": True, "reason": body.reason, "by": user.username},
        rule_version="human-override",
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    ))
    db.add(AuditLog(
        user_id=user.id,
        action="PRIORITY_OVERRIDE",
        target_type="INCIDENT",
        target_id=incident.incident_id,
        previous_value={"priority": previous},
        new_value={"priority": body.priority},
        reason=body.reason,
    ))
    db.commit()
    return {"incident_id": incident.incident_id, "previous": previous, "priority": body.priority, "reason": body.reason}


def _get_or_404(db: Session, incident_id: str) -> Incident:
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Incident not found"})
    return incident