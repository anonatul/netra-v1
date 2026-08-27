"""Lifecycle — field updates (HUMAN-class evidence) with recalculation triggers
(FR-033/FR-087): every update re-runs priority + zones + recommendations."""
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.auth.deps import get_current_user  # noqa: F401 (kept for parity with KB API)
from app.clustering.service import recompute_zones
from app.models import AuditLog, FieldUpdate, Incident, User
from app.priority.service import apply_priority
from app.recommend.service import suggest

UPDATE_HANDLERS = {
    "VERIFY": lambda inc, v: _setattr(inc, "status", "VERIFIED"),
    "RESCUED": lambda inc, v: (_setattr(inc, "status", "RESCUED"), _setattr(inc, "resolved_at", datetime.now(timezone.utc))),
    "FALSE": lambda inc, v: (_setattr(inc, "status", "FALSE"), _setattr(inc, "resolved_at", datetime.now(timezone.utc))),
    "VICTIM_COUNT": lambda inc, v: _setattr(inc, "victim_estimate", int(v.get("count")) if v.get("count") else None),
    "ACCESS": lambda inc, v: _merge_vuln(inc, "access_issue", bool(v.get("blocked"))),
    "MEDICAL": lambda inc, v: _merge_vuln(inc, "medical_critical", bool(v.get("critical"))),
    "NOTE": lambda inc, v: None,
}


def _setattr(inc: Incident, key: str, value) -> bool:
    setattr(inc, key, value)
    return True


def _merge_vuln(inc: Incident, key: str, value: bool) -> bool:
    vuln = dict(inc.vulnerability or {})
    if value:
        vuln[key] = True
    else:
        vuln.pop(key, None)
    inc.vulnerability = vuln
    return True


def apply_field_update(
    db: Session, incident: Incident, update_type: str, values: dict, notes: str | None, user: User
) -> dict:
    handler = UPDATE_HANDLERS.get(update_type)
    if handler is None:
        raise ValueError(f"Unknown update_type: {update_type}")

    previous = {
        "status": incident.status,
        "victim_estimate": incident.victim_estimate,
        "vulnerability": incident.vulnerability,
    }
    handler(incident, values)

    db.add(FieldUpdate(
        incident_id=incident.incident_id,
        user_id=user.id,
        update_type=update_type,
        values=values,
        notes=notes,
        sync_state="SYNCED",
    ))
    db.add(AuditLog(
        user_id=user.id,
        action=f"FIELD_UPDATE_{update_type}",
        target_type="INCIDENT",
        target_id=incident.incident_id,
        previous_value=previous,
        new_value={"status": incident.status, "victim_estimate": incident.victim_estimate},
        reason=notes,
    ))

    if update_type == "VERIFY":
        incident.confidence = round(min(0.98, (incident.confidence or 0.5) + 0.1), 3)
        incident.location_confidence = round(min(1.0, (incident.location_confidence or 0.5) + 0.1), 3)

    # Recalculation triggers (FR-033): priority → recommendation → zones
    incident.updated_at = datetime.now(timezone.utc)
    priority = apply_priority(db, incident, source="FIELD_UPDATE")
    if incident.status not in ("RESCUED", "FALSE"):
        suggest(db, incident, overwrite=True)
        recompute_zones(db)
    db.commit()

    return {
        "incident_id": incident.incident_id,
        "status": incident.status,
        "priority": priority["level"],
        "priority_reasons": priority["reasons"],
    }