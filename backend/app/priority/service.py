"""Rescue Priority Score — the core innovation (docs/PRIORITY.md, AD-004).

Transparent, explainable, versioned. Weights live in PRIORITY_WEIGHTS so the
model can be versioned/tuned without code changes (model_versions table).

Hysteresis (FR-074): escalation immediate; de-escalation needs a sustained drop
below the hysteresis floor, not the entry threshold.
"""
import math
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Incident, PriorityScore

PRIORITY_VERSION = settings.priority_rules_version

PRIORITY_WEIGHTS = {
    "severity": 0.30,
    "vulnerability": 0.20,
    "victims": 0.15,
    "freshness": 0.15,
    "location_confidence": 0.10,
    "access": 0.10,
}

SEVERITY_VALUE = {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.75, "CRITICAL": 1.0, "UNKNOWN": 0.3}

# Entry thresholds and hysteresis floors (P1→P2 at <0.68, not <0.55)
LEVELS = [
    ("P1", 0.75, 0.68),
    ("P2", 0.55, 0.48),
    ("P3", 0.35, 0.30),
]
P4_FLOOR = 0.35

FRESHNESS_HALF_LIFE_HOURS = 4.0
CORROBORATION_MAX_SOURCES = 5
CORROBORATION_BOOST_MAX = 1.25


def _freshness(last_evidence_at: datetime | None, now: datetime | None = None) -> float:
    if last_evidence_at is None:
        return 0.0
    now = now or datetime.now(timezone.utc)
    if last_evidence_at.tzinfo is None:
        last_evidence_at = last_evidence_at.replace(tzinfo=timezone.utc)
    hours = max(0.0, (now - last_evidence_at).total_seconds() / 3600.0)
    return 2 ** (-hours / FRESHNESS_HALF_LIFE_HOURS)


def _victims_score(estimate: int | None) -> float:
    if estimate is None:
        return 0.0
    return min(1.0, math.log10(max(1, estimate)) / 2.0)  # log scale: 1→0, 10→0.5, 100→1


def _vulnerability_score(vulnerability: dict | None) -> float:
    vuln = vulnerability or {}
    critical = any(vuln.get(k) for k in ("elderly", "child", "mobility_issue", "pregnant"))
    return 1.0 if critical else 0.0


def level_for_score(score: float) -> str:
    if score >= LEVELS[0][1]:
        return "P1"
    if score >= LEVELS[1][1]:
        return "P2"
    if score >= LEVELS[2][1]:
        return "P3"
    return "P4"


def compute_score(incident: Incident, now: datetime | None = None) -> dict:
    """Compute full explainable score. Returns {score, level, reasons, components, boost}."""
    now = now or datetime.now(timezone.utc)
    reasons: list[dict] = []

    severity = SEVERITY_VALUE.get(incident.severity or "UNKNOWN", 0.3)
    reasons.append({"factor": "severity", "weight": PRIORITY_WEIGHTS["severity"], "value": severity,
                    "evidence": [incident.severity], "note": f"consensus severity {incident.severity}"})

    vuln = _vulnerability_score(incident.vulnerability)
    vuln_keys = [k for k, v in (incident.vulnerability or {}).items() if v]
    reasons.append({"factor": "vulnerability", "weight": PRIORITY_WEIGHTS["vulnerability"], "value": vuln,
                    "evidence": vuln_keys, "note": "elderly/child/mobility/pregnant present" if vuln else "no vulnerable indicators"})

    victims = _victims_score(incident.victim_estimate)
    reasons.append({"factor": "victims", "weight": PRIORITY_WEIGHTS["victims"], "value": victims,
                    "evidence": [incident.victim_estimate], "note": "log-scale estimate"})

    fresh = _freshness(incident.last_evidence_at, now)
    reasons.append({"factor": "freshness", "weight": PRIORITY_WEIGHTS["freshness"], "value": round(fresh, 4),
                    "evidence": [str(incident.last_evidence_at)], "note": f"half-life {FRESHNESS_HALF_LIFE_HOURS}h decay"})

    loc = incident.location_confidence or 0.5
    reasons.append({"factor": "location_confidence", "weight": PRIORITY_WEIGHTS["location_confidence"], "value": loc,
                    "evidence": [incident.location_accuracy_m], "note": "from location accuracy"})

    access = 1.0 if (incident.vulnerability or {}).get("access_issue") else 0.0
    reasons.append({"factor": "access", "weight": PRIORITY_WEIGHTS["access"], "value": access,
                    "evidence": ["access_issue"] if access else [], "note": "access problem reported" if access else "no access problem reported"})

    components = {
        "severity": severity,
        "vulnerability": vuln,
        "victims": victims,
        "freshness": round(fresh, 4),
        "location_confidence": loc,
        "access": access,
    }

    score = sum(PRIORITY_WEIGHTS[f] * components[f] for f in PRIORITY_WEIGHTS)

    sources = min(incident.independent_source_count or 0, CORROBORATION_MAX_SOURCES)
    boost = 1.0 + (sources - 1) * ((CORROBORATION_BOOST_MAX - 1.0) / (CORROBORATION_MAX_SOURCES - 1.0))
    boost = max(1.0, min(boost, CORROBORATION_BOOST_MAX))
    if sources > 1:
        reasons.append({"factor": "corroboration", "value": round(boost, 3),
                        "evidence": [f"{incident.independent_source_count} independent sources"],
                        "note": "independent evidence multiplier"})

    score = min(1.0, score * boost)
    return {
        "score": round(score, 4),
        "level": level_for_score(score),
        "components": components,
        "corroboration_boost": round(boost, 3),
        "reasons": reasons,
        "rule_version": PRIORITY_VERSION,
    }


def apply_hysteresis(current_level: str | None, new_score: float) -> str:
    """FR-074: escalations are immediate; de-escalations require the floor."""
    new_level = level_for_score(new_score)
    if current_level in (None, "UNRATED"):
        return new_level
    rank = {"P1": 3, "P2": 2, "P3": 1, "P4": 0}
    if rank[new_level] >= rank[current_level]:
        return new_level
    for level, threshold, floor in LEVELS:
        if level == current_level and new_score >= floor:
            return current_level
    return new_level


def apply_priority(db: Session, incident: Incident, source: str = "SYSTEM") -> dict:
    """Compute + persist priority with hysteresis; stores versioned history row."""
    result = compute_score(incident)
    result["level"] = apply_hysteresis(incident.priority, result["score"])
    result["hysteresis_applied"] = incident.priority not in (None, "UNRATED") and result["level"] != level_for_score(result["score"])

    db.add(PriorityScore(
        incident_id=incident.incident_id,
        score=result["score"],
        level=result["level"],
        reasons=result,
        rule_version=PRIORITY_VERSION,
        model_version=None,
        timestamp=datetime.now(timezone.utc),
    ))
    incident.priority = result["level"]
    db.commit()
    return result