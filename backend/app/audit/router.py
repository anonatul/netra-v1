"""Audit API (FR-051, NFR-032) — append-only trail, AUDITOR/ADMIN only."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_role
from app.database import get_db
from app.models import AuditLog, User

router = APIRouter()


@router.get("/audit")
def audit_log(
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("AUDITOR", "ADMIN")),
) -> dict:
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    if target_type:
        q = q.filter(AuditLog.target_type == target_type)
    if target_id:
        q = q.filter(AuditLog.target_id == target_id)
    rows = q.limit(limit).all()
    return {
        "count": len(rows),
        "entries": [
            {
                "id": r.id,
                "user_id": r.user_id,
                "action": r.action,
                "target_type": r.target_type,
                "target_id": r.target_id,
                "previous_value": r.previous_value,
                "new_value": r.new_value,
                "reason": r.reason,
                "timestamp": r.timestamp,
            }
            for r in rows
        ],
    }