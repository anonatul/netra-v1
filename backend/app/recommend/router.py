"""Recommendation API — suggest + operator decision (docs/API.md)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_role
from app.database import get_db
from app.models import AuditLog, Incident, Recommendation, User
from app.recommend.service import suggest
from app.schemas import RecommendationDecisionIn

router = APIRouter()


@router.get("/incidents/{incident_id}/recommendation")
def get_recommendation(incident_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> dict:
    incident = _get_or_404(db, incident_id)
    latest = (
        db.query(Recommendation)
        .filter(Recommendation.incident_id == incident_id)
        .order_by(Recommendation.id.desc())
        .first()
    )
    if latest is None:
        return suggest(db, incident)
    return {
        "recommendation_id": latest.id,
        "resources": latest.resources,
        "reasons": latest.reasons,
        "rule_version": latest.rule_version,
        "status": latest.status,
        "created_at": latest.created_at,
        "resolved_at": latest.resolved_at,
    }


@router.post("/incidents/{incident_id}/recommendation/decision")
def decide_recommendation(
    incident_id: str,
    body: RecommendationDecisionIn,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("OPERATOR", "COMMANDER", "ADMIN")),
) -> dict:
    incident = _get_or_404(db, incident_id)
    latest = (
        db.query(Recommendation)
        .filter(Recommendation.incident_id == incident_id, Recommendation.status == "SUGGESTED")
        .order_by(Recommendation.id.desc())
        .first()
    )
    if latest is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "No pending recommendation"})
    latest.status = body.status
    latest.resolved_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    db.add(AuditLog(
        user_id=user.id,
        action="RECOMMENDATION_DECISION",
        target_type="INCIDENT",
        target_id=incident.incident_id,
        new_value={"status": body.status},
    ))
    db.commit()
    return {"recommendation_id": latest.id, "status": body.status}


def _get_or_404(db: Session, incident_id: str) -> Incident:
    incident = db.query(Incident).filter(Incident.incident_id == incident_id).first()
    if incident is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Incident not found"})
    return incident