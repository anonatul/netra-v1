# NETRA — AI Strategy

> Mirrors KB file 12 (AI/ML Architecture) + AD-006. **AI is an assistive component, never a single point of failure, and never in the emergency critical path.**

## Three-Layer AI

```text
Layer 1  Deterministic safety rules      ALWAYS ON · zero latency · auditable
Layer 2  Lightweight local classifier    TF-IDF + SGD (scikit-learn), EN/HI/Hinglish
Layer 3  LLM gateway (Qwen3.6-35B-A3B)   ASYNC enrichment · off critical path · optional
```

## Layer 1 — Deterministic Safety Rules (always on)

Multilingual keyword lexicons (English, Hindi, Hinglish; Marathi extension later):

| Attribute | English | Hindi / Hinglish |
|-----------|---------|------------------|
| trapped | trapped, stuck, can't get out | phans gaye, phas gaye, bahar nahi nikal |
| medical-critical | bleeding, injured, unconscious, heart | khoon, ghaayal, be-hosh, dil |
| elderly | grandmother, grandfather, elderly, old | dadi, dada, buddhe, bujurg |
| child | baby, child, kid | bachcha, bachchi, shishu |
| mobility | cannot walk, wheelchair | chal nahi sakta/sakti, wheelchair |
| pregnant | pregnant | garbhvati, pet me bachcha |
| water-intrusion | water entering, water inside | paani ghus, paani andar |
| water-rising | water rising, water up to | paani badh raha, paani kamar tak |
| roof/terrace | rooftop, terrace | chhat par, terrace par |
| road-blocked | road blocked, no road | sadak band, raasta band |
| safe | safe, rescued, reached shelter, fine | safe, bach gaye, theek hoon, shelter pahunch |

Every hit emits: `{attribute, value, confidence (1.0), model: "rules-v1", source_terms[]}`.

Rules output = baseline. LLM can only **raise** confidence or add attributes rules cannot infer (victim counts, nuanced severity, location hints).

## Layer 2 — Local Classifier (optional, trained)

- Features: char n-grams TF-IDF (works for Hinglish/romanized Hindi)
- Targets (multi-label): `trapped`, `medical_critical`, `elderly`, `child`, `mobility_issue`, `water_rising`, `safe`
- Trained on synthetic labelled set (~10k) + hand-labelled core (~300)
- If sklearn unavailable/untrained → Layer 1 only, confidence unchanged
- Deterministic at inference (fixed seed, no dropout)

## Layer 3 — LLM Gateway (TCET CoE AI Gateway)

| Setting | Value |
|---------|-------|
| Base URL | `https://ai.tcetcercd.in/v1` (from docs/ai-gateway.md) |
| Model | `qwen3.6-35b-a3b` (verify via GET /v1/models) |
| Auth | Bearer `AI_GATEWAY_API_KEY` (env only) |
| Format | OpenAI-compatible chat completions, JSON output mode |
| Timeout | 2.5 s · max 1 retry · async via job queue |
| Batching | queue workers; rate-limited (campus fair-use) |

Prompt contract (stable, versioned `llm-extract-v1`):

```text
You are an emergency-triage extraction engine. Extract from the distress
message (may be Hinglish/multilingual). Return ONLY JSON:
{"disaster":"FLOOD|EARTHQUAKE|CYCLONE|OTHER|UNKNOWN",
 "severity":"LOW|MEDIUM|HIGH|CRITICAL",
 "trapped":bool, "medical_critical":bool, "elderly":bool, "child":bool,
 "mobility_issue":bool, "pregnant":bool, "water_rising":bool,
 "victim_count":int|null, "access_issue":bool,
 "location_hint":string|null,
 "confidence":0.0-1.0, "reasoning":string|null}
```

LLM output stored as DERIVED evidence: `{prediction, confidence, model_version: "qwen3.6-35b-a3b-llm-extract-v1", timestamp}`.

## Fallback Chain (FR-011, NFR-005, R-08)

```text
LLM unavailable / timeout / invalid JSON
        ↓
Layer 2 (if trained) — reduced confidence
        ↓
Layer 1 rules — base confidence
        ↓
attribute confidence drops; if critical attributes unresolved
        ↓
UNRESOLVED → human review queue (FR-085)
```

**LLM failure never suppresses an emergency. Never blocks ingestion.**

## AI Decision Rule (judge-critical, file 12 §4)

AI is justified only when it materially beats rules on a measured metric:

```text
Rules: 91% F1 vs AI: 92% F1  → AI not justified (10× cost)
Rules: 65% F1 vs AI: 89% F1  → AI justified
```

Our benchmark (`docs/BENCHMARK.md`) reports L1 vs L1+L2 vs L1+L3 on the labelled set. We expect the LLM to win on victim-count extraction, nuance, and Hinglish — that is the evidence for "why AI."

## Evaluation (NFR-038/039/040)

| Capability | Metric |
|------------|--------|
| Severity classification | precision / recall / F1 |
| Vulnerability detection | precision / recall / F1 |
| Victim count extraction | precision / recall / MAE |
| Location extraction | exact match / distance error |
| Duplicate detection | precision / recall / F1 |
| False-critical rate | % incorrectly marked P1 |

## Golden AI Rule

> LLM output = evidence, not truth. Every output carries prediction + confidence + model version. AI failure → rules → human review. Never silence an emergency.