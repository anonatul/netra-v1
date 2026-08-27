"""Rescue Priority Score unit tests (docs/PRIORITY.md)."""
from datetime import datetime, timedelta, timezone

from app.models import Incident
from app.priority.service import apply_hysteresis, compute_score, level_for_score


def _incident(**kw) -> Incident:
    defaults = {
        "incident_id": "test-1",
        "severity": "HIGH",
        "vulnerability": {"elderly": True},
        "victim_estimate": 5,
        "location_confidence": 0.8,
        "location_accuracy_m": 50,
        "independent_source_count": 1,
        "evidence_count": 1,
        "last_evidence_at": datetime.now(timezone.utc),
        "priority": None,
    }
    defaults.update(kw)
    return Incident(**defaults)


def test_p1_critical_case():
    inc = _incident(severity="CRITICAL", vulnerability={"elderly": True, "child": True},
                    victim_estimate=10, independent_source_count=3)
    r = compute_score(inc)
    assert r["score"] > 0.8
    assert r["level"] == "P1"
    assert any(rev["factor"] == "corroboration" for rev in r["reasons"])
    assert r["rule_version"] == "priority-v1.0"


def test_low_priority_minimal_evidence():
    inc = _incident(severity="LOW", vulnerability={}, victim_estimate=None,
                    independent_source_count=1, last_evidence_at=datetime.now(timezone.utc) - timedelta(hours=24))
    r = compute_score(inc)
    assert r["level"] == "P4"


def test_freshness_decay():
    fresh = _incident(last_evidence_at=datetime.now(timezone.utc))
    stale = _incident(last_evidence_at=datetime.now(timezone.utc) - timedelta(hours=8))
    assert compute_score(fresh)["components"]["freshness"] > compute_score(stale)["components"]["freshness"]


def test_victims_log_scale():
    assert compute_score(_incident(victim_estimate=1))["components"]["victims"] == 0.0
    assert compute_score(_incident(victim_estimate=100))["components"]["victims"] == 1.0


def test_level_for_score_thresholds():
    assert level_for_score(0.8) == "P1"
    assert level_for_score(0.6) == "P2"
    assert level_for_score(0.4) == "P3"
    assert level_for_score(0.2) == "P4"


def test_hysteresis_blocks_quick_downgrade():
    # P1 stays P1 while score stays above the 0.68 floor
    assert apply_hysteresis("P1", 0.70) == "P1"
    # Drops below the floor → downgrades
    assert apply_hysteresis("P1", 0.65) == "P2"


def test_hysteresis_escalation_immediate():
    assert apply_hysteresis("P3", 0.80) == "P1"


def test_explainability_has_reasons_for_every_weight():
    r = compute_score(_incident())
    factors = {rev["factor"] for rev in r["reasons"] if rev["factor"] != "corroboration"}
    assert factors == {"severity", "vulnerability", "victims", "freshness", "location_confidence", "access"}