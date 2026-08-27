# NETRA — KB Traceability Matrix

> Maps every KB requirement to a build component, test, and demo. Updated continuously. This is the audit trail that answers "where is the evidence?"

## Legend

`FR-0xx` functional requirement (file 07) · `NFR-0xx` non-functional (file 08) · `AD-0xx` architecture decision (file 24)

## Core Capability Families (file 07 §99)

| Family | FRs | Component | Test | Demo |
|--------|-----|-----------|------|------|
| INGEST | FR-001, 002, 004, 005 | `ingestion/` | TC-ING | Killer scenario T+00–T+02 |
| UNDERSTAND | FR-009, 010, 011 | `extraction/` (L1/L2/L3) | TC-NLP | F1 benchmark table |
| CONSOLIDATE | FR-013, 014, 015 | `fusion/` | TC-DEDUP | 30 dupes → 1 source |
| LOCATE | FR-016, 017, 018 | `fusion/` + `clustering/` | TC-LOC | Confidence radius on map |
| PRIORITIZE | FR-029, 030, 031, 033 | `priority/` | TC-PRI | Zone escalation to P1 |
| RECOMMEND | FR-035, 036 | `recommend/` | TC-REC | Boats + medical suggestion |
| OPERATE | FR-038…044 | `lifecycle/`, API, frontend | TC-FIELD | RESCUED off queue |
| SURVIVE FAILURE | FR-046…050, 085, 086 | fallbacks everywhere | TC-FAIL | Kill LLM, cut network |

## Key FR → Component

| FR | Requirement | Component | Status |
|----|-------------|-----------|--------|
| FR-002 | Emergency evidence ingestion | `ingestion/router.py` | ✅ |
| FR-006 | Raw evidence preservation | `models.py` Event immutable | ✅ |
| FR-009 | Multilingual incident extraction | `extraction/` | ✅ |
| FR-010 | NLP confidence | `extraction/` output schema | ✅ |
| FR-011 | Rule-based fallback | `extraction/rules.py` | ✅ |
| FR-015 | Independent source count | `fusion/service.py` | ✅ |
| FR-017 | Location confidence | `fusion/service.py` + accuracy radius | ✅ |
| FR-021 | Incident confidence | `fusion/service.py` | ✅ |
| FR-024 | No-signal safety rule | `priority/freshness.py` | ✅ |
| FR-025 | Spatial clustering (uncertainty) | `clustering/` + Python haversine matching | ✅ |
| FR-029 | Rescue priority P1–P4 | `priority/service.py` | ✅ |
| FR-031 | Explainable priority | `priority/service.py` reasons | ✅ |
| FR-034 | Human override | `priority/router.py` + audit | ✅ |
| FR-035 | Resource recommendation | `recommend/` | ✅ |
| FR-043 | Incident status states | `lifecycle/` | ✅ |
| FR-044 | Field verification | `lifecycle/` | ✅ |
| FR-046 | Offline local operation | local deployment + L1 rules; external map/LLM can degrade | Partial |
| FR-051 | Audit logging | `audit/router.py` + AuditLog | ✅ |
| FR-052/053 | Auth + RBAC | `auth/` | ✅ |
| FR-065 | Simulation mode | `simulation/` | ✅ |
| FR-066 | Scenario replay | `simulation/engine.py` | ✅ |
| FR-070 | Explainability | priority + recommend outputs | ✅ |
| FR-084 | No autonomous life-critical action | workflow gates | ✅ |

## Key NFR → Component

| NFR | Requirement | Component | Status |
|-----|-------------|-----------|--------|
| NFR-001 | E2E latency P95 ≤ 5s | benchmark harness | ⬜ |
| NFR-005 | Graceful AI degradation | `extraction/` fallback chain | ✅ |
| NFR-007 | Crash recovery | SQLAlchemy persistence, no volatile state | ✅ |
| NFR-010 | Idempotent processing | `ingestion/router.py` | ✅ |
| NFR-013 | Offline operation | local deployment | ⬜ |
| NFR-017 | Connectivity awareness | frontend status bar | ✅ |
| NFR-028/029 | Auth + authorization | `auth/` | ✅ |
| NFR-032 | Auditability | `audit/router.py` | ✅ |
| NFR-045/046 | Model/rule versioning | `model_versions`, `rule_versions` tables | ✅ |
| NFR-062 | UI usability under stress | frontend design system | ✅ |
| NFR-067 | Fail closed | `tests/test_security.py` | ✅ |
| NFR-096 | Demo not dependent on live APIs | local-first + L1 fallback | ✅ |
| NFR-097 | Deterministic demo | seed 42 + replay | ✅ |
| NFR-099 | Observable AI failure | status bar LLM health | ✅ |

## AD Status (mirror of file 24)

| AD | Decision | Component | Status |
|----|----------|-----------|--------|
| AD-001 | Modular monolith | `backend/app/` module layout | ✅ |
| AD-002 | PostgreSQL + PostGIS | PostGIS Docker image; scalar coordinates in current ORM | Partial |
| AD-003 | One queue mechanism | DB-backed jobs | ✅ |
| AD-004 | Rescue Priority Score = core | `priority/` | ✅ |
| AD-005 | Adaptive clustering | `clustering/` | ✅ |
| AD-006 | Three-layer AI | L1 `extraction/` + optional L3 `llm/`; L2 not implemented | Partial |
| AD-007 | Human-in-the-loop | workflow gates + UI | ✅ |
| AD-008 | Connectivity state machine | shared state + frontend | ✅ |
| AD-009 | Local-first demo | deployment | ⬜ |
| AD-010 | Adapters + common event model | common event model; real channel adapters not implemented | Partial |
| AD-011 | Rule-based recommendations | `recommend/` | ✅ |
| AD-012 | Incident as central object | `models.py` | ✅ |
| AD-013 | No custom telecom/femtocell | (rejected, not built) | ✅ N/A |
| AD-014 | Benchmark vs baselines | `benchmark/` | ✅ |

## Golden Traceability Rule

> Every claimed metric must link: Requirement → Component → Test → Demo → Result. No link, no claim.