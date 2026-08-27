# Free Hosting — NETRA

Everything is already env-driven, so a free cloud deploy is a few clicks.

## 1. Backend + Postgres — Render (free)
1. Push this repo to GitHub.
2. render.com → *New* → *Blueprint* → connect the repo.
3. `render.yaml` is detected automatically:
   - creates a **free Postgres** DB,
   - deploys the backend (free web service, auto `DATABASE_URL`),
   - runs `python -m scripts.init_db` on release (creates tables + seeds `commander/commander123`, `admin/admin123`, `auditor/auditor123`, `citizen-sim/citizen-sim123`).
4. The campus Qwen works **if the backend runs where it can reach `ai.tcetcercd.in/v1`**. Off-campus it just degrades to rules-only.

> Free tier caveat: the service sleeps after 15 min idle → first request has a ~30s cold start.

## 2. Frontend — Vercel / Netlify (free, no cold start)
- Vercel: import repo, it reads `vercel.json`. Replace `<YOUR-BACKEND-ON-RENDER>` in `vercel.json` with your real backend URL, then deploy.
  - `VITE_API_BASE` is set at build time → frontend calls the backend directly (no proxy needed).
- Netlify: same, set build command `cd frontend && npm run build`, publish `frontend/dist`, and set `VITE_API_BASE` env.

## 3. Routes
- `/` dashboard (commander/commander123)
- `/sim` simulation console (presenter)
- `/victim` citizen QR
- `/logs` audit terminal (admin/admin123)

## 4. Local run (no cloud)
```
# backend
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m scripts.init_db
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
# frontend
cd frontend && npm install && npm run dev -- --host 0.0.0.0
```
(env vars: copy `.env.example` → `.env` if needed)
