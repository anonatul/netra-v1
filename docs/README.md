# NETRA — Network-resilient Emergency Triage and Response Assistance

> **NETRA is a disaster-response intelligence layer that fuses fragmented citizen distress signals from existing emergency channels into confidence-ranked, severity-scored rescue zones and actionable resource requirements for responders.**

## Positioning

NETRA does **NOT** replace ERSS-112, SACHET, Cell Broadcast or emergency-location services. It sits on top of them and turns their fragmented, high-volume signals into a live operational rescue picture.

```text
SACHET / Cell Broadcast  →  Warn people
ERSS-112 / ELS           →  Emergency intake + location
NETRA                    →  Fuse evidence + prioritize rescue decisions
NDRF / SDRF              →  Act on prioritized zones
```

## The Problem

> The problem is not "too many messages"; the problem is "too little reliable decision information extracted from too many uncertain messages."

## Core Innovation — Rescue Priority Score

A transparent, explainable, versioned priority model over:

```
severity × victim count × vulnerability × recency × location confidence × accessibility × corroboration
```

with **independent-evidence counting** (84 messages ≠ 84 victims), incident fusion, adaptive uncertainty-aware clustering, and evidence-backed explainable resource recommendations. The prototype uses deterministic L1 rules on the critical path with optional asynchronous L3 enrichment; human-in-the-loop: AI recommends, responders decide.

## Quick Start

See `docs/PLAN.md` and the root `README.md` for run instructions.

## Document Index

| File | Content |
| ---- | ------- |
| `PLAN.md` | Build plan, phases, definition of done |
| `KB-TRACEABILITY.md` | KB requirement → component → test → demo mapping |
| `SCHEMA.md` | Database schema + data classes |
| `API.md` | API contract |
| `AI.md` | 3-layer AI strategy + LLM gateway design |
| `PRIORITY.md` | Rescue Priority Score specification |
| `BENCHMARK.md` | Benchmark methodology + expected metrics |
| `DEMO.md` | Demo script + adversarial scenarios + recovery |
| `SECURITY.md` | Security & privacy checklist |
| `DECISIONS.md` | Build-time architecture decision log |
| `EVALUATION.md` | Self-score vs SIH judge criteria (target 83–85) |
| `ai-gateway.md` | TCET CoE AI Gateway guide — **gitignored, contains API key** |

## Golden Rule

> Never say "NETRA works when the entire cellular network is down." Always say: "NETRA turns the fragmented emergency signals of existing systems into prioritized rescue operations, and degrades gracefully as connectivity degrades."