# NETRA — Rescue Priority Score Specification

> The core innovation (AD-004). A transparent, explainable, versioned priority model. Version: `priority-v1.0` (weights draft — calibrated on synthetic scenarios + expert review per file 04 §10).

## Score Formula

```text
RescueScore = Σ wᵢ · fᵢ          i ∈ {severity, vulnerability, victims,
                                        freshness, location_confidence, access, corroboration}
```

## Components

| # | Factor | Weight (draft) | Source | Range |
|---|--------|---------------|--------|-------|
| 1 | severity | 0.30 | extracted severity (L1/L2/L3 consensus) | 0..1 |
| 2 | vulnerability | 0.20 | elderly/child/mobility/pregnant present | 0..1 |
| 3 | victim_count | 0.15 | estimate (normalized, log scale) | 0..1 |
| 4 | freshness | 0.15 | exponential decay of last evidence | 0..1 |
| 5 | location_confidence | 0.10 | evidence quality (KB file 15 §6 table) | 0..1 |
| 6 | access | 0.10 | access issue reported (road blocked etc.) | 0..1 |
| 7 | corroboration | boost ×1.0..1.25 | independent-source count (≤5 capped) | multiplier |

**Freshness decay:** `f = 2^(-hours / half_life)`, `half_life` = disaster-configurable (flood default 4h).
**Never:** lack of new signals ⇒ safe. Decay lowers freshness only (FR-024).

**Severity mapping:** LOW=0.25, MEDIUM=0.5, HIGH=0.75, CRITICAL=1.0 (consensus across layers; LLM can upgrade rules' LOW→MEDIUM only with high confidence).

## Thresholds → Levels

| Score | Level | Meaning |
|-------|-------|---------|
| ≥ 0.75 | P1 — CRITICAL | immediate attention |
| ≥ 0.55 | P2 — HIGH | timely response |
| ≥ 0.35 | P3 — MODERATE | monitor + respond |
| < 0.35 | P4 — LOW | monitor |
| — | UNRATED | insufficient evidence (human review) |

## Hysteresis (FR-074 — prevent oscillation)

- P1 → P2 only if score drops below **0.68** (not 0.55): requires a *sustained* change, not a wiggle
- P2 → P3 requires drop below 0.48
- Escalations are immediate (safety bias)
- Same incident can change at most 2 levels per hour without human confirmation

## Explainability (FR-031, FR-070)

Every priority output includes:

```jsonc
{
  "level": "P1",
  "score": 0.81,
  "rule_version": "priority-v1.0",
  "reasons": [
    {"factor": "severity", "value": 1.0, "evidence": ["sms-001(L3)", "field-002"]},
    {"factor": "vulnerability", "value": 1.0, "evidence": ["sms-001: dadi"]},
    {"factor": "victim_count", "value": 0.6, "evidence": ["L3 estimate 5"]},
    {"factor": "freshness", "value": 0.98, "evidence": ["last evidence 3 min ago"]},
    {"factor": "location_confidence", "value": 0.9, "evidence": ["ELS ±50m"]},
    {"factor": "access", "value": 1.0, "evidence": ["field: road blocked"]}
  ],
  "corroboration_boost": 1.2,
  "computed_at": "2026-08-18T09:15:00Z"
}
```

## Recalculation Triggers (FR-033, FR-087)

- new evidence / field update / verification
- status change
- incident merge/split
- disaster configuration change

## Fallback Mode (FR-050)

If priority module fails: `P = f(severity, victim_count, freshness)` with simple rules → still explainable, lower fidelity, flagged `priority: FALLBACK`.

## Golden Priority Rule

> P1 must always answer "why": medical-critical indicators, vulnerable victims, recent corroborated evidence, high location confidence, restricted access. Never "P1 because AI says so."