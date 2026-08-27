# NETRA — Build Plan

> Status: ACTIVE · Target: internal judge demo · Window: ~12–14 working days · Solo build + review

## Locked Decisions (from KB)

| # | Decision | KB Source |
|---|----------|-----------|
| 1 | Modular monolith: FastAPI + PostgreSQL + React (Vite); PostGIS image reserved for spatial migration | AD-001, AD-002, file 16 |
| 2 | Rescue Priority Score = core innovation, explainable + versioned | AD-004 |
| 3 | Adaptive uncertainty-aware clustering, never fixed 50m | AD-005, R-12 |
| 4 | Implemented AI path: L1 rules (always-on) → optional L3 LLM (async, off critical path); L2 local classifier is not in this prototype | AD-006, R-08 |
| 5 | One queue mechanism (DB-backed jobs); Redis optional | AD-003 |
| 6 | Connectivity state machine, visible in UI | AD-008, file 14 |
| 7 | Local-first, offline-capable, deterministic scenario replay | AD-009, NFR-096/097 |
| 8 | Benchmark vs baselines (raw count / rules / manual) — no invented numbers | AD-014, file 19/20 |
| 9 | Auth + RBAC + audit + fail-closed | file 13 |
| 10 | Incident (not message) = central object; independent-source counting | AD-012, FR-015 |
| 11 | No femtocell / 2G-survives / full-blackout / autonomous-dispatch claims | R-01…R-14 |
| 12 | Every decision traceable: evidence → interpretation → priority → human action | file 06 §44 |

## Stack

```text
Backend : Python 3.14, FastAPI, SQLAlchemy 2, psycopg3, Pydantic v2
DB      : PostgreSQL 16 (PostGIS image; scalar lat/lon in current schema)
AI      : L1 deterministic rules (lexicons) · L3 Qwen3.6-35B-A3B via
          TCET CoE AI Gateway (OpenAI-compatible), async and optional
Frontend: Vite + React + TypeScript + Tailwind + MapLibre GL JS + OpenFreeMap
Queue   : DB-backed async jobs (no Kafka/RabbitMQ)
Deploy  : docker compose (postgis) + local uvicorn + vite dev/build
```

## Phases

| Phase | Days | Deliverable | Judge evidence |
|-------|------|-------------|----------------|
| 0. Infra + docs | 1 | docs/ (12 files), compose, .env, scaffold, /healthz | Repeatable startup (NFR-071) |
| 1. Data model | 2 | 12 tables per KB file 10, RAW/DERIVED/SYSTEM/HUMAN tagging, scalar coordinate fields | Schema doc matches runtime |
| 2. Ingestion | 3 | POST /events, adapters, validation, idempotency, timestamps | No duplicate events (NFR-010) |
| 3. L1 rules | 4 | Multilingual lexicons, deterministic extraction, always-on | Zero-latency fallback |
| 4. L2 + L3 AI | 5 | Local classifier + LLM adapter (JSON mode, timeout, fallback) | F1 benchmark L1 vs L1+LLM |
| 5. Location/fusion | 6 | Location confidence, dedup, independent-source counting | 30 dupes → 1 source |
| 6. Clustering | 7 | Adaptive uncertainty-aware DBSCAN, zone builder | "Why 50m?" answer |
| 7. Priority + recommend | 8 | Rescue Priority Score, explainability, hysteresis, resource rules | Explainable P1/P2 100% |
| 8. Lifecycle/audit/auth | 9 | State machine, field updates, overrides, RBAC, audit | Traceability tests |
| 9. Frontend | 10–11 | Tactical dashboard: queue, MapLibre map+heatmap, drawer, status bar, sim bar | Demo script runnable |
| 10. Simulation | 12 | Killer scenario + 5 adversarial, deterministic replay | Same input → same output |
| 11. Benchmark | 13 | 10k labelled generator, baselines A/B/C, metrics export | docs/benchmark_results.md |
| 12. QA + demo pack | 14 | Integration pass, recovery script, Q&A drills, self-score | Rehearsed demo 3× |

## Definition of Done (whole project)

- [ ] Golden path works end-to-end (file 09 §89: report → incident → zone → P1 → rec → verify → resolve)
- [ ] F1 benchmark produced: L1 rules vs L1+L3 LLM, on labelled multilingual set
- [ ] Manual-vs-NETRA benchmark recorded honestly (triage time, duplicate reduction)
- [ ] Adversarial: fake-SOS burst reduces confidence; 30 dupes = 1 source; stale ≠ safe
- [ ] AI kill → rule fallback + human-review queue; network cut → OFFLINE mode keeps working
- [ ] Restart recovery: no critical state lost
- [ ] Auth + RBAC + audit operational; fail-closed verified
- [ ] Dashboard: queue, map + heatmap + confidence radius, incident drawer, evidence, timeline, recommendations, filters, status bar, sim controls
- [ ] Deterministic scenario replay (seed 42)
- [ ] `docker compose up` + documented run guide; frontend builds clean
- [ ] All 12 docs written, KB-traceability maintained
- [ ] Demo rehearsed 3× incl. kill-LLM + cut-network; recovery script proven

## Cut Ladder (if time runs short)

1. ✂ L2 local classifier (L1+LLM only)
2. ✂ Redis (remove from compose)
3. ✂ Extra languages beyond EN/HI/Hinglish
4. ✂ Alerting / search / advanced filters
5. ✂ 10k → 3k labelled dataset (documented limitation)

**Never cut:** priority engine, explainability, independent-source counting, adaptive clustering, offline mode, deterministic replay, benchmark, auth.