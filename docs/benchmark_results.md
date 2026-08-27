# NETRA — Benchmark Results

> Generated 2026-08-17 19:17 UTC — dataset: 11730 reports, seed 42.

## Dataset composition

| Language | Count |
|----------|-------|
| en | 5478 |
| hi | 3703 |
| hinglish | 2549 |

Profiles: 12 labelled emergency profiles + FAKE + SAFE.

## L1 rules pipeline (deterministic, always-on)

- Throughput: **41892.9 reports/sec** (single process, no LLM)
- Severity classification macro-F1: **0.5074**
- Victim-count MAE: **1.309**

### Attribute detection (precision / recall / F1)

| Attribute | Precision | Recall | F1 |
|-----------|-----------|--------|-----|
| trapped | 0.9641 | 0.7795 | 0.862 |
| medical_critical | 0.0 | 0.0 | 0.0 |
| elderly | 1.0 | 0.8504 | 0.9191 |
| child | 1.0 | 0.9822 | 0.991 |
| mobility_issue | 0.4808 | 0.9974 | 0.6488 |
| pregnant | 1.0 | 0.9679 | 0.9837 |
| water_rising | 0.9117 | 0.3469 | 0.5026 |
| access_issue | 1.0 | 0.5905 | 0.7425 |

- Safe-message detection F1: **0.4694**
- Fake-SOS detection F1: **1.0**

## L1 + L3 (LLM) sample comparison

- LLM sample: 150 reports, 114 succeeded, 226.45s
- Severity macro-F1: rules **0.5074** vs rules+LLM **0.5462**
- Victim-count MAE: rules **1.309** vs rules+LLM **1.406**

| Attribute | Rules F1 | Rules+LLM F1 |
|-----------|----------|--------------|
| trapped | 0.862 | 0.8736 |
| medical_critical | 0.0 | 1.0 |
| elderly | 0.9191 | 1.0 |
| child | 0.991 | 1.0 |
| mobility_issue | 0.6488 | 0.5 |
| pregnant | 0.9837 | 1.0 |
| water_rising | 0.5026 | 0.8056 |
| access_issue | 0.7425 | 0.2524 |

**AI decision rule:** AI justified

## Limitations

- Synthetic labelled data generated from templates (ground truth by construction).
- Human baseline pending (manual triage of a 200-report sample, timed).
- LLM numbers are a sample; campus gateway latency affects throughput.

## Load test (NFR-001: E2E latency P95 ≤ 5s)

- Burst: **2400 events** (8 concurrent workers) against a dedicated instance
- Throughput: **16.1 events/sec**
- Latency: p50 **743.6ms** · p95 **917.5ms** · p99 **968.8ms** · max **1099.0ms**
- Errors: 0 · events landed: 2000 (map-data display cap) · incidents created: 278
- **NFR-001 verdict: PASS** (P95 917.5ms ≤ 5000ms) — LLM enrichment stays off the critical path (async queue); rate limiting was disabled on this instance only (guard verified separately).
- Concurrency hardening: the first burst run surfaced a genuine race — two concurrent zone recomputes deadlocked (`UPDATE incidents` → `DELETE operational_zones` in opposite lock orders). Fixed with a transaction-scoped advisory lock (`pg_advisory_xact_lock`) serializing recomputes; second run: 0 deadlocks. Remaining bottleneck is the O(n²) per-event zone recompute (16.1 events/s at 2.4k incidents); per-event cost is negligible at demo scale.
