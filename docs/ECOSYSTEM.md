# NETRA — Ecosystem Research (KB file 03)

> Validated 2026-08-18 against current primary sources (PIB, MHA, DoT, C-DOT, SDMA). Defines where NETRA sits, what already exists, and the gap it fills.

## 1. The 2026 Indian emergency-response stack (official layer)

| System | What it does | Direction | Status (2026) |
|--------|--------------|-----------|---------------|
| **ERSS-112** (MHA) | Unified single emergency number; PSAP + Computer-Aided Dispatch (CAD) with GIS map terminals; call-taker → dispatcher workflow | **Inbound, call-centric** | Sup. Court ordered all helplines (100/101/102/108/1033/1091) merged into 112 within 3 months (28 May 2026); Delhi live 19 Jan 2026; 20 states/UTs by Feb 2026 |
| **Cell Broadcast System (CBS)** | C-DOT geo-targeted, multilingual, 2G–5G alerts that override DND and work during congestion; cannot be disabled; reads alerts aloud | **Outbound broadcast** | Launched 2 May 2026, integrated with SACHET; nationwide test reached all networks |
| **SACHET** | NDMA's CAP-based alert platform + dashboard/app for disaster managers to moderate/send alerts | **Outbound** | Operational all 36 states/UTs; ~134B SMS alerts sent during cyclones/floods/heatwaves |
| **Web-DCRA & DSS** | Dynamic Composite Risk Atlas + Decision Support System for cyclone planning | Planning | Used in cyclones Biparjoy, Michaung |
| **NDRF / NCMC** | 16 battalions, 28 regional response centres; national command | Response org | — |

**Key point:** the official ecosystem is excellent at *warning citizens* (CBS/SACHET, out) and *receiving one emergency call* (112, voice-led). The 112 stack's "10 channels" include SMS/SOS/chatbot/media-crawler/IoT/WhatsApp — but everything funnels to a **human call-taker**, who triages each item manually.

## 2. The crowdsourcing / crisis-mapping layer

- **Ushahidi** (Kenya 2008 → Haiti 2010, ~hundreds of deployments): citizen SMS/USSD/WhatsApp/web reports mapped in real time; proved the *demand* for inbound text crowdsourcing. Limitation (documented): unverified crowdsourced data is hard to trust for official decision-making.
- **Kerala floods 2018** — the canonical Indian proof: ad-hoc IT + social-media crowdsourcing drove rescue; volunteers manually triangulated thousands of messages. It worked *because people donated manual labour* — not because triage was automated.
- **Google Crisis Response / OpenStreetMap** — situational awareness, not a triage engine.

## 3. The gap (where NETRA fits)

> Everything above is either **push (authority → citizen)** or **manual pull (call-taker reads one message at a time)**. Nothing does **automated inbound triage of a message flood at command-and-control speed.**

1. **Volume:** a flood generates thousands of SMS/SOS texts in minutes (Kerala 2018 had tens of thousands). A PSAP has call-takers, not an NLP fusion layer.
2. **Duplicates:** 20–40% of distress texts describe the same incident (measured in NETRA's own dataset). Manual review = wasted responder time.
3. **Priority:** "building collapse, 2 trapped" buried under 500 "paani aa raha hai" messages. No automated Rescue Priority Score exists at the SEOC.
4. **Trust:** crisis-mapping exists but isn't wired into official CAD/GIS dispatch — accuracy/confidence unquantified.
5. **Resilience:** 112 relies on voice + app; cell towers and power fail. A degraded-mode, local-first triage engine that keeps working without connectivity is absent.

## 4. NETRA positioning (integration, not replacement)

- **Sits between the ERSS-112 inbound channels and the dispatcher** — the triage/fusion layer the 2026 ecosystem lacks: ingest SMS/SOS/WhatsApp/social/text → dedupe → geo-cluster into operational zones → Rescue Priority Score → GIS map for the CAD terminal.
- **Complements CBS/SACHET**: CBS pushes warnings *out* to citizens; NETRA pulls and triages their replies *in* — the two halves of one loop.
- **Feeds existing tools** (SACHET, Web-DCRA, PSAP CAD) via API; does not replace NDMA/SDMA.
- **Adversarial by design**: fake-SOS detection, confidence-weighted clustering, LLM-failure fallback — because crisis-mapping's documented weakness (unverified data) is the exact problem a command system must not inherit.

## 5. Evidence of demand (why now)

- SC order forcing one-112 integration (2026) = national push toward unified response infrastructure → they will need the triage layer.
- CBS launch (2026) = alerts now reach every phone → inbound volume will rise → triage becomes the bottleneck.
- Kerala 2018 crowdsourcing validated citizen-text reporting at scale.
- SIH problem statements repeatedly target flood/city-disaster response tooling; judges reward systems that integrate with (not duplicate) official infra.

## Sources

- MHA PIB "Innovative Methods to Save People From Disasters" (11 Mar 2025) — ERSS-112 disaster extension, SACHET dashboard, Web-DCRA, NDRF.
- MHA ERSS page — "ONE INDIA ONE EMERGENCY NUMBER 112", 10 inbound channels, PSAP + GIS CAD.
- News18 (29 May 2026) / Notopedia (1 Jun 2026) — Supreme Court 28-May-2026 order integrating 100/101/108/102/1033/1091 into 112; Delhi live 19 Jan 2026; 20 states/UTs.
- PIB / NewsOnAir / DoT (2 May 2026) — Cell Broadcast System launch, C-DOT SACHET integration, 134B alerts, geo-targeted 2G–5G.
- C-DOT CBS product page — CAP-based SACHET integration, WSIS 2024 / SKOCH 2025.
- Crawford (2026), *Policy Innovations from the Global South* (Palgrave) — Ushahidi case study, SMS/USSD/WhatsApp channels, Haiti 2010.
- KSDMA IRP (2020) — Kerala floods crowdsourcing rescue model.
