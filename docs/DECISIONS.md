# NETRA — Build Decision Log

> Append-only. Mirrors KB file 24 (AD log) + file 28 (journey log). Every build-time decision recorded with reason; revisit only with new evidence.

## 2026-08-18 — Project kickoff (build mode)

- ✅ **BD-001 — Start fresh in NETRAv1.** No code reuse from earlier NETRA prototype; rebuild per KB to guarantee architecture traceability. Reason: KB mandates modular monolith + PostGIS + 3-layer AI; earlier prototype diverged (SQLite, different stack).
- ✅ **BD-002 — LLM via TCET CoE AI Gateway** (docs/ai-gateway.md): OpenAI-compatible `https://ai.tcetcercd.in/v1`, model qwen3.6-35b-a3b. Used as Layer 3 enrichment ONLY; critical path deterministic (R-08). Key in `.env`, gateway doc gitignored.
- ✅ **BD-003 — MapLibre GL JS + OpenFreeMap vector tiles** (Google-like UX) + native heatmap layer + offline dark-grid fallback. Reason: no API key needed, offline-capable, Mapbox-grade rendering (NFR-096). Google Maps API swap possible via provider abstraction.
- ✅ **BD-004 — PostGIS via dedicated docker container** `netra-postgres` (postgis/postgis:16-3.4), port 5433 to avoid collision with existing tasknest-postgres on 5432.
- ✅ **BD-005 — DB-backed job queue** for async LLM + reprocessing (no Redis/Kafka/RabbitMQ). Reason: AD-003, MVP scale.
- ✅ **BD-006 — Priority weights draft** `priority-v1.0` (severity .30, vulnerability .20, victims .15, freshness .15, location .10, access .10, corroboration ×1.0–1.25) — pending calibration on synthetic scenarios + expert review.
- ✅ **BD-007 — Vite + React + TypeScript + Tailwind** for frontend (not Next.js). Reason: SPA dashboard, single page, fast dev, simple static build.
- ✅ **BD-008 — Synthetic dataset generator (seed 42)** produces 10k labelled reports + adversarial packs; benchmark exports honest results to docs/benchmark_results.md.

## Open Items (mirror KB file 28)

- [ ] Verify ERSS actual capabilities (fusion/NLP/priority) — could kill differentiation
- [ ] Validate location+distress feasibility under realistic partial degradation
- [ ] Build + label synthetic multilingual dataset
- [ ] Run manual-vs-NETRA benchmark (honest)
- [ ] Expert review of priority model
- [ ] Demo scenario replay complete

## Golden Log Rule

> Log what was decided and why, so every claim has a trail — and never repeat a rejected idea.