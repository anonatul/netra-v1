#!/usr/bin/env bash
# NETRA — start the whole stack for a demo (docs/README.md)
# db (postgis) -> backend (:8001) -> frontend (:5173)
set -euo pipefail

cd "$(dirname "$0")/.."

echo "== 1/3 database =="
docker compose up -d db
sleep 2

echo "== 2/3 backend =="
cd backend
if pgrep -f "[u]vicorn app.main" > /dev/null; then
  echo "backend already running on :8001"
else
  nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/netra-uvicorn.log 2>&1 &
  sleep 3
  curl -s http://localhost:8001/healthz && echo
fi

echo "== 3/3 frontend =="
cd ../frontend
if pgrep -f "[v]ite" > /dev/null; then
  echo "frontend already running on :5173"
else
  nohup npm run dev > /tmp/netra-vite.log 2>&1 &
  sleep 3
  curl -s -o /dev/null -w "frontend http://localhost:5173 -> %{http_code}\n" http://localhost:5173/
fi

echo
echo "Demo: open http://localhost:5173 (commander/commander123),"
echo "then run scripts/demo_reset.sh for a fresh killer scenario."