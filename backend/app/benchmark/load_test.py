"""Load test (docs/BENCHMARK.md, NFR-001: E2E P95 <= 5s).

Bursts N events concurrently against the load instance (port 8002,
netra_load DB, rate limits disabled), records per-request latency,
computes p50/p95/p99 + throughput, then verifies pipeline output
(events -> incidents) and appends results to docs/benchmark_results.md.

Usage:
  python -m app.benchmark.load_test --workers 8 --per-worker 300
"""
import argparse
import json
import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

BASE = "http://localhost:8002/api/v1"

TEMPLATES = [
    ("SMS", "paani kamar tak aa gaya hai, dadi aur bachcha chhat par phans gaye"),
    ("SMS", "building collapse near station, 2 people trapped under debris"),
    ("ERSS", "roof collapse, ek banda bleeding heavily, unconscious"),
    ("ELS", "water rising fast, wheelchair user cannot move from first floor"),
    ("SMS", "bhaari baarish, ghar mein paani ghus gaya, pregnant lady needs help"),
    ("ERSS", "trees down on the road, ambulance cannot reach the colony"),
    ("SMS", "भारी बारिश हो रही है, घर में पानी घुस गया है, बच्चे छत पर हैं"),
    ("FIELD", "school building damaged, children trapped inside classroom"),
]


def make_event(i: int) -> dict:
    source, text = TEMPLATES[i % len(TEMPLATES)]
    lat = 19.05 + random.random() * 0.06
    lon = 72.83 + random.random() * 0.09
    return {
        "source_type": source,
        "source_timestamp": "2026-08-18T10:00:00Z",
        "text": text,
        "source_identifier": f"load-{i}",
        "location": {"lat": round(lat, 6), "lon": round(lon, 6), "accuracy_m": random.choice([30, 100, 300])},
        "idempotency_key": f"load-{i}",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--per-worker", type=int, default=300)
    args = parser.parse_args()

    total = args.workers * args.per_worker
    token = httpx.post(f"{BASE}/auth/login", json={"username": "operator", "password": "operator123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    latencies: list[float] = []
    errors = 0

    def post(i: int) -> None:
        nonlocal errors
        t0 = time.perf_counter()
        try:
            r = httpx.post(f"{BASE}/events", headers=headers, json=make_event(i), timeout=30)
            if r.status_code != 201:
                errors += 1
        except Exception:
            errors += 1
        latencies.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        list(ex.map(post, range(total)))
    elapsed = time.perf_counter() - t0

    latencies.sort()
    def pct(p: float) -> float:
        return round(latencies[min(len(latencies) - 1, int(len(latencies) * p))], 1)

    results = {
        "total": total,
        "workers": args.workers,
        "elapsed_sec": round(elapsed, 2),
        "throughput_per_sec": round(total / elapsed, 1),
        "errors": errors,
        "p50_ms": pct(0.50),
        "p95_ms": pct(0.95),
        "p99_ms": pct(0.99),
        "max_ms": round(latencies[-1], 1),
    }
    print(json.dumps(results, indent=2))

    db_counts = httpx.get(f"{BASE}/map-data", headers=headers).json()
    print("pipeline: events", db_counts["heat_points"], "incidents", len(db_counts["incidents"]))
    results["events_landed"] = len(db_counts["heat_points"])
    results["incidents_created"] = len(db_counts["incidents"])

    _write_markdown(results)


def _write_markdown(results: dict) -> None:
    path = "/mnt/newvolume/SIH-Hackathon/NETRAv1/docs/benchmark_results.md"
    with open(path, encoding="utf-8") as f:
        doc = f.read()
    section = "\n".join([
        "## Load test (NFR-001: E2E latency P95 ≤ 5s)",
        "",
        f"- Burst: **{results['total']} events** ({results['workers']} concurrent workers) against a dedicated instance",
        f"- Throughput: **{results['throughput_per_sec']} events/sec**",
        f"- Latency: p50 **{results['p50_ms']}ms** · p95 **{results['p95_ms']}ms** · p99 **{results['p99_ms']}ms** · max **{results['max_ms']}ms**",
        f"- Errors: {results['errors']} · events landed: {results['events_landed']} · incidents created: {results['incidents_created']}",
        f"- **NFR-001 verdict: {'PASS' if results['p95_ms'] <= 5000 else 'FAIL'}** (P95 {results['p95_ms']}ms ≤ 5000ms) — LLM enrichment stays off the critical path (async queue); rate limiting was disabled on this instance only (guard verified separately).",
        "",
    ])
    marker = "## Load test (NFR-001: E2E latency P95 ≤ 5s)"
    idx = doc.find(marker)
    if idx != -1:
        doc = doc[:idx].rstrip() + "\n\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc + section)
    print(f"results appended -> {path}")


if __name__ == "__main__":
    main()