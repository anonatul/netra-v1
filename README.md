# NETRA — Network-resilient Emergency Triage and Response Assistance

**NETRA is a disaster-response intelligence layer that fuses fragmented citizen distress signals from existing emergency channels into confidence-ranked, severity-scored rescue zones and actionable resource requirements for responders.**

It does **NOT** replace ERSS-112, SACHET, Cell Broadcast or emergency-location services — it sits on top of them.

## Quick Start

```bash
# everything at once (db + backend + frontend)
./scripts/start_all.sh
# then open http://localhost:5173 (login: commander / commander123)
```

Or step by step:

```bash
# 1. Infrastructure (PostGIS database)
docker compose up -d

# 2. Backend (port 8001)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env        # then fill in secrets
uvicorn app.main:app --port 8001

# 3. Frontend
cd frontend
npm install
npm run dev                    # http://localhost:5173
```

## Demo

```bash
# fresh state + killer scenario (deterministic, seed 42) — exact counts verified:
# 50 reports -> 17 incidents -> 6 zones -> 2 P1 / 3 P2 / 1 P3
./scripts/demo_reset.sh
```

See `docs/DEMO.md` for the full script and `docs/` for all project context.

## Repo Layout

```
docs/        project context: plan, traceability, schema, API, AI, priority,
             benchmark, demo, security, decisions, evaluation (+ gitignored ai-gateway.md)
backend/     FastAPI modular monolith
frontend/    Vite + React + TypeScript + Tailwind + MapLibre GL
```

## Golden Rule

> Never say "NETRA works when the entire cellular network is down." Always say: "NETRA turns the fragmented emergency signals of existing systems into prioritized rescue operations, and degrades gracefully as connectivity degrades."