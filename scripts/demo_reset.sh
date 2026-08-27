#!/usr/bin/env bash
# NETRA — one-command demo reset (docs/DEMO.md, NFR-097 deterministic seed 42)
# Usage: scripts/demo_reset.sh   (expects backend on :8001)
set -euo pipefail

BASE="http://localhost:8001/api/v1"

echo "== NETRA demo reset =="
read -r -s -p "commander password: " PASS; echo
TOKEN=$(curl -s -X POST "$BASE/auth/login" -H 'Content-Type: application/json' \
  -d "{\"username\":\"commander\",\"password\":\"$PASS\"}" | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -X POST "$BASE/sim/reset" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}'
echo
curl -s -X POST "$BASE/sim/scenario/start" -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"scenario_id":"killer","seed":42}' | python3 -m json.tool
echo
echo "== expected: 50 reports -> 17 incidents -> 6 zones -> 2 P1 / 3 P2 / 1 P3 =="
curl -s "$BASE/map-data" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
from collections import Counter
d=json.load(sys.stdin)
z=Counter(z['priority'] for z in d['zones'])
print('zones:',len(d['zones']),dict(z),'| incidents:',len(d['incidents']),dict(Counter(i['priority'] for i in d['incidents'])))"
echo
echo "Next: press STEP in the dashboard (or:)"
read -r -p "run step now? [y/N] " -n 1; echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  curl -s -X POST "$BASE/sim/scenario/step" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' -d '{}' | head -c 120; echo
  curl -s "$BASE/map-data" -H "Authorization: Bearer $TOKEN" | python3 -c "
import sys,json
from collections import Counter
d=json.load(sys.stdin)
z=Counter(z['priority'] for z in d['zones'])
print('after step -> zones:',len(d['zones']),dict(z),'(expect 3 P1 / 2 P2 / 1 P3)')"
fi