# NETRA — Evaluation Self-Score

> Mirrors KB file 00 §6. Target: 67 → 83–85 before the judge demo. Updated as evidence lands.

| Dimension | Current | Target | Evidence needed |
|-----------|:-------:|:------:|-----------------|
| Problem | 9 | 9 | KB file 01 ✅ |
| Understanding | 9 | 9 | validated ecosystem research (file 03 = docs/ECOSYSTEM.md, 2026 sources) |
| Innovation | 6 | 8 | Rescue Priority Score demo + ablation F1 (benchmark: rules 0.51 → +LLM 0.55, medical_critical 0.0 → 1.0) |
| Technical feasibility | 6 | 8 | working golden path + benchmark (37 tests, L1 43k reports/s) |
| Adoption | 5 | 7 | integration-layer positioning + RBAC/audit (audit API live) |
| Impact | 9 | 9 | problem framing |
| Scalability | 8 | 8 | modular monolith + measured load test (NFR-001 PASS: 2400 evts, P95 917ms, deadlock found+fixed) |
| Cost | 6 | 8 | local-first, open-source stack, campus LLM |
| Security | 6 | 8 | file 13 checklist complete + tests (rate limits + audit live) |
| Demo | 9 | 9 | deterministic replay + adversarial pack (verified exact counts) |
| **Total** | **73** | **83–85** | — |

## Verdict To Fix (file 00 §7)

> "The pitch sounds better than the underlying technical novelty currently is."

Fix = demonstrate: Rescue Priority Score on real-time pipeline, LLM ablation benchmark, adversarial robustness, traceability from evidence to decision.

## Golden Evidence Rule

> The gap between screening and winning is evidence. Measure the improvement, or the pitch is just a map.