"""Recommendations — explainable resource suggestions (docs/API.md).

Deterministic rules from incident state; every suggestion carries reasons.
"""
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Incident, Recommendation

RULE_VERSION = "recommend-v1"


def suggest(db: Session, incident: Incident, overwrite: bool = True) -> dict:
    resources: list[dict] = []
    reasons: list[str] = []
    vuln = incident.vulnerability or {}
    severity = incident.severity or "UNKNOWN"

    if vuln.get("water_rising") or vuln.get("trapped") or incident.severity in ("HIGH", "CRITICAL"):
        resources.append({"resource": "RESCUE_BOATS", "quantity": _boats(incident), "priority": "high"})
        reasons.append("water rising / trapped reports require water rescue assets")

    if severity in ("HIGH", "CRITICAL") or vuln.get("mobility_issue") or vuln.get("elderly") or vuln.get("child"):
        resources.append({"resource": "MEDICAL_TEAM", "quantity": 1, "priority": "high"})
        reasons.append("medical-critical indicators or vulnerable victims on scene")

    if vuln.get("pregnant"):
        resources.append({"resource": "AMBULANCE", "quantity": 1, "priority": "critical"})
        reasons.append("pregnant person reported — ambulance stand-by")

    if vuln.get("access_issue"):
        resources.append({"resource": "ROAD_CLEARANCE", "quantity": 1, "priority": "medium"})
        reasons.append("access problem reported — route clearance may be needed")

    if incident.severity in ("LOW", "MEDIUM", "UNKNOWN") and not vuln:
        resources.append({"resource": "SHELTER_INFORMATION", "quantity": 1, "priority": "low"})
        reasons.append("no critical indicators — informational guidance")

    if not resources:
        return {"resources": [], "reasons": [], "rule_version": RULE_VERSION}

    if overwrite:
        db.query(Recommendation).filter(
            Recommendation.incident_id == incident.incident_id,
            Recommendation.status == "SUGGESTED",
        ).update({"status": "SUPERSEDED"})

    rec = Recommendation(
        incident_id=incident.incident_id,
        resources=resources,
        reasons=reasons,
        rule_version=RULE_VERSION,
        status="SUGGESTED",
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return {"recommendation_id": rec.id, "resources": rec.resources, "reasons": rec.reasons,
            "rule_version": rec.rule_version, "status": rec.status}


def _boats(incident: Incident) -> int:
    """1 boat per 8 estimated victims, min 1, max 4."""
    victims = incident.victim_estimate or 1
    return max(1, min(4, (victims + 7) // 8))