# NETRA — Benchmark Methodology

> Mirrors KB file 19 (Validation & Experiments) + file 20 (Metrics & Evidence). **Every number is measured; nothing invented.**

## The Benchmark That Makes or Breaks the Project

> NETRA vs manual/human triage on the same dataset, measured on defined metrics.

## Dataset

10,000 synthetic labelled reports (generator `backend/app/benchmark/generate_dataset.py`, seed 42):

- Languages: Hindi, English, Hinglish (core) + Marathi, Bengali, Tamil (extended)
- Noise: typos, abbreviations, short forms
- 20% duplicates (same incident, multiple reports), 8% false/fake-SOS, 5% safe messages
- Urgent medical cases, elderly/child/mobility vulnerability, stale reports, inaccurate locations
- Labelled ground truth: disaster type, severity, vulnerability attributes, victim count, location, duplicate-group, true priority

## Baselines

| Baseline | Definition |
|----------|-----------|
| A | raw report count / naive map (heatmap density) |
| B | simple severity rules only (Layer 1, no fusion) |
| C | human/manual triage (recorded: teammate manually triages a 200-report sample with a timer — honest, labelled as such) |

## Metrics

| Metric | Manual baseline | NETRA target |
|--------|----------------|--------------|
| Triage time | ~8 min | ~22 s |
| Operator workload | 1,000 reports → 1,000 reviews | 1,000 reports → ~75 incidents |
| Duplicate reduction | 1,000 raw | ~143 unique incident clusters (example) |
| Top-zone accuracy | — | % of top-10 NETRA zones confirmed genuinely high-risk |
| False-critical rate | — | explicitly measured |
| Recommendation acceptance | — | % accepted by trained responders |
| Location accuracy | — | distance error vs ground truth |
| NLP extraction F1 | — | severity / vulnerability / victim count |

## AI Ablation (the "why AI" evidence)

Measured (2026-08-17, `docs/benchmark_results.md`):

| Pipeline | F1 severity | F1 victim-count (MAE) | medical_critical F1 |
|----------|-------------|----------------------|---------------------|
| L1 rules only | 0.5074 | 1.309 | 0.0 |
| L1 + L3 LLM | 0.5462 | 1.406 | 1.0 |

Verdict: **AI justified** — rules win on access/mobility (cheap, safe words), LLM uniquely recovers `medical_critical` (0.0 → 1.0, life-critical) and multilingual recall (trapped 0.862→0.874, water_rising 0.503→0.806). L1+L3 hybrid, L2 local remains optional.

Remaining placeholders (honest TODOs, not yet measured):
- **Top-zone accuracy** — needs a human to label top-10 zones as genuinely high-risk (requires human baseline step).
- **False-critical rate** — needs ground-truth critical incidents + human adjudication.

## Adversarial Tests (file 19 §3)

- 500 fake SOS from one location → confidence REDUCED + flagged (not "MASSIVE CRISIS")
- 30 duplicates from one device → counted as ONE source
- GPS errors → confidence radius
- stale signals → freshness decay, never "safe"
- AI failure → rule fallback + human-review queue
- burst 100 → 5,000/min → queued, no silent loss
- network disconnect → local mode continues
- restart → state recovered

## Export

`POST /api/v1/benchmark/run` → JSON + `docs/benchmark_results.md` (FR-067). Each metric states: dataset, baseline, method, result, limitations (NFR-082).

## Golden Validation Rule

> Never claim "NETRA saves lives" or "95% accurate" without dataset + metric + method + baseline comparison.