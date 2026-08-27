"""LLM enrichment — L3 async pass over an event (docs/AI.md).

Merges LLM output into evidence as DERIVED data with model version + confidence.
Rules (L1) are never overwritten downwards: LLM can only raise confidence or add
attributes rules could not infer. On LLM failure, event stays PROCESSED with L1
data and the failure is recorded — never UNRESOLVED (R-08).
"""
from sqlalchemy.orm import Session

from app.clustering.service import recompute_zones
from app.extraction.rules import extract
from app.llm.gateway import extract_with_llm
from app.models import Event, Evidence, Incident
from app.priority.service import apply_priority
from app.recommend.service import suggest

SEVERITY_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4, "UNKNOWN": 0}
MODEL_VERSION = "qwen3.6-35b-a3b-llm-extract-v1"
MIN_CONFIDENCE_TO_OVERRIDE_RULES = 0.7


def enrich_event(db: Session, event_id: str) -> dict | None:
    """Run L3 enrichment; return merge summary or None on failure."""
    event = db.query(Event).filter(Event.event_id == event_id).first()
    if event is None or not event.text:
        return None

    rules_result = extract(event.text)
    llm_result = extract_with_llm(event.text)
    if llm_result is None:
        return {"event_id": event_id, "llm": "failed", "merged": False}

    evidence = (
        db.query(Evidence).filter(Evidence.event_id == event_id).order_by(Evidence.id.desc()).first()
    )
    if evidence is None:
        return {"event_id": event_id, "llm": "no-evidence", "merged": False}

    rules_extraction = dict(evidence.extraction or {})
    rules_extraction["llm"] = {
        "result": llm_result,
        "model_version": MODEL_VERSION,
        "llm_confidence": llm_result.get("confidence"),
        "status": "merged",
    }

    attrs = dict(rules_extraction.get("attributes") or {})
    merged_any = False
    for key in ("trapped", "medical_critical", "elderly", "child", "mobility_issue", "pregnant", "water_rising", "access_issue"):
        if llm_result.get(key) is True:
            attrs[key] = {
                "value": True,
                "confidence": llm_result.get("confidence", 0.5),
                "model": MODEL_VERSION,
                "source_terms": ["llm"],
            }
            merged_any = True
    rules_extraction["attributes"] = attrs

    llm_sev = llm_result.get("severity", "UNKNOWN")
    if (llm_sev != "UNKNOWN" and SEVERITY_RANK.get(llm_sev, 0) > SEVERITY_RANK.get(rules_extraction.get("severity"), 0)
            and llm_result.get("confidence", 0) >= MIN_CONFIDENCE_TO_OVERRIDE_RULES):
        rules_extraction["severity"] = llm_sev
        rules_extraction["severity_override"] = "llm"
        merged_any = True

    if llm_result.get("victim_count") and not rules_extraction.get("victim_hint"):
        rules_extraction["victim_hint"] = llm_result["victim_count"]
        rules_extraction["victim_source"] = MODEL_VERSION
        merged_any = True

    evidence.extraction = rules_extraction
    evidence.confidence = max(evidence.confidence or 0.5, llm_result.get("confidence", 0.5))

    if merged_any:
        incident = db.query(Incident).filter(Incident.incident_id == evidence.incident_id).first()
        if incident:
            _merge_into_incident(incident, rules_extraction, llm_result)
            apply_priority(db, incident, source="LLM_ENRICH")
            suggest(db, incident, overwrite=True)
            recompute_zones(db)

    db.commit()
    return {"event_id": event_id, "llm": "ok", "merged": merged_any, "severity": rules_extraction.get("severity")}


def _merge_into_incident(incident: Incident, extraction: dict, llm_result: dict) -> None:
    severity = extraction.get("severity")
    if severity and severity != "UNKNOWN" and SEVERITY_RANK[severity] > SEVERITY_RANK.get(incident.severity or "UNKNOWN", 0):
        incident.severity = severity

    attrs = extraction.get("attributes") or {}
    vuln = dict(incident.vulnerability or {})
    for key, spec in attrs.items():
        if key in ("elderly", "child", "mobility_issue", "pregnant", "medical_critical"):
            vuln[key] = True
    incident.vulnerability = vuln

    victim = extraction.get("victim_hint")
    if victim and (incident.victim_estimate is None or victim > incident.victim_estimate):
        incident.victim_estimate = victim