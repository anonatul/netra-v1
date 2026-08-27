"""Benchmark harness (docs/BENCHMARK.md) — measured, honest numbers.

Runs L1 rules over the labelled dataset; optionally L3 (LLM) on a sample.
Metrics: severity macro-F1, per-attribute precision/recall/F1, victim-count MAE,
safe/fake detection. Writes docs/benchmark_results.md.

Usage:
  python -m app.benchmark.harness --reports reports.jsonl
  python -m app.benchmark.harness --reports reports.jsonl --llm-sample 200
"""
import argparse
import json
import time

from app.extraction.rules import extract

SEVERITY_LEVELS = ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNKNOWN"]
ATTR_KEYS = ["trapped", "medical_critical", "elderly", "child", "mobility_issue",
             "pregnant", "water_rising", "access_issue"]


def _severity_level(sev: str) -> str:
    return sev if sev in SEVERITY_LEVELS else "UNKNOWN"


def f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0


def _cm(y_true: list[bool], y_pred: list[bool]) -> tuple[int, int, int, int]:
    tp = sum(1 for t, p in zip(y_true, y_pred) if t and p)
    fp = sum(1 for t, p in zip(y_true, y_pred) if not t and p)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t and not p)
    tn = len(y_true) - tp - fp - fn
    return tp, fp, fn, tn


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    return round(p, 4), round(r, 4), round(f1(p, r), 4)


def run_rules(rows: list[dict]) -> list[dict]:
    out = []
    for row in rows:
        r = extract(row["text"])
        attrs = {k: bool((r["attributes"] or {}).get(k, {}).get("value")) for k in ATTR_KEYS}
        out.append({
            "severity": _severity_level(r["severity"]),
            "attrs": attrs,
            "victims": r["victim_hint"],
            "safe": r["safe"],
            "fake": r["fake"],
        })
    return out


def _rules_metrics(rows: list[dict], preds: list[dict]) -> dict:
    severity_truth = [_severity_level(r["severity"]) for r in rows]
    severity_pred = [p["severity"] for p in preds]
    macro_f1s = []
    for level in SEVERITY_LEVELS:
        yt = [s == level for s in severity_truth]
        yp = [s == level for s in severity_pred]
        tp, fp, fn, _ = _cm(yt, yp)
        macro_f1s.append(_prf(tp, fp, fn))
    sev_f1 = round(sum(f for _, _, f in macro_f1s) / len(macro_f1s), 4)

    attr_metrics = {}
    for key in ATTR_KEYS:
        yt = [bool(r["attrs"].get(key)) for r in rows]
        yp = [p["attrs"][key] for p in preds]
        tp, fp, fn, _ = _cm(yt, yp)
        attr_metrics[key] = dict(zip(("precision", "recall", "f1"), _prf(tp, fp, fn)))

    victim_mae = round(
        sum(abs((r["victims"] or 0) - (p["victims"] or 0)) for r, p in zip(rows, preds)) / len(rows), 3
    )

    safe_tp, safe_fp, safe_fn, _ = _cm([r["safe"] for r in rows], [p["safe"] for p in preds])
    fake_tp, fake_fp, fake_fn, _ = _cm([r["fake"] for r in rows], [p["fake"] for p in preds])

    return {
        "severity_macro_f1": sev_f1,
        "severity_per_level": {lvl: m for lvl, m in zip(SEVERITY_LEVELS, macro_f1s)},
        "attributes": attr_metrics,
        "victim_count_mae": victim_mae,
        "safe_detection": dict(zip(("precision", "recall", "f1"), _prf(safe_tp, safe_fp, safe_fn))),
        "fake_detection": dict(zip(("precision", "recall", "f1"), _prf(fake_tp, fake_fp, fake_fn))),
    }


def _llm_metrics(rows: list[dict], llm_rows: dict) -> dict:
    """LLM sample metrics — aligned by text (only rows with LLM results)."""
    preds = []
    matched_rows = []
    for row in rows:
        r = llm_rows["results"].get(row["text"])
        if r is None:
            continue
        matched_rows.append(row)
        attrs = {k: bool(r.get(k)) for k in ATTR_KEYS}
        preds.append({
            "severity": _severity_level(r.get("severity") or "UNKNOWN"),
            "attrs": attrs,
            "victims": r.get("victim_count"),
            "safe": False, "fake": False,
        })
    return _rules_metrics(matched_rows, preds)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reports", type=str, required=True)
    parser.add_argument("--llm-sample", type=int, default=0)
    parser.add_argument("--out", type=str, default="../../docs/benchmark_results.md")
    args = parser.parse_args()

    rows = [json.loads(line) for line in open(args.reports, encoding="utf-8")]
    t0 = time.time()
    preds = run_rules(rows)
    rules_elapsed = round(time.time() - t0, 2)

    metrics = _rules_metrics(rows, preds)
    metrics["throughput_per_sec"] = round(len(rows) / rules_elapsed, 1)

    llm_metrics = None
    if args.llm_sample > 0:
        from app.llm.gateway import extract_with_llm

        sample = [r for r in rows if not r["fake"] and not r["safe"]][: args.llm_sample]
        results = {}
        t0 = time.time()
        for row in sample:
            r = extract_with_llm(row["text"])
            if r:
                results[row["text"]] = r
        llm_elapsed = round(time.time() - t0, 2)
        llm_metrics = _llm_metrics(sample, {"results": results, "rows": sample})
        llm_metrics["calls"] = len(sample)
        llm_metrics["succeeded"] = len(results)
        llm_metrics["elapsed_sec"] = llm_elapsed

    _write_markdown(args.out, rows, metrics, llm_metrics)
    print(f"benchmark written -> {args.out} (rules throughput {metrics['throughput_per_sec']}/s)")


def _write_markdown(path: str, rows: list[dict], metrics: dict, llm_metrics: dict | None) -> None:
    n = len(rows)
    langs = {}
    for r in rows:
        langs[r["lang"]] = langs.get(r["lang"], 0) + 1
    lines = [
        "# NETRA — Benchmark Results",
        "",
        f"> Generated {__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} — dataset: {n} reports, seed 42.",
        "",
        "## Dataset composition",
        "",
        "| Language | Count |",
        "|----------|-------|",
    ]
    for lang, count in sorted(langs.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {lang} | {count} |")
    lines += [
        "",
        f"Profiles: {len(set(r['profile'] for r in rows if r['profile'] not in ('FAKE', 'SAFE')))} labelled emergency profiles + FAKE + SAFE.",
        "",
        "## L1 rules pipeline (deterministic, always-on)",
        "",
        f"- Throughput: **{metrics['throughput_per_sec']} reports/sec** (single process, no LLM)",
        f"- Severity classification macro-F1: **{metrics['severity_macro_f1']}**",
        f"- Victim-count MAE: **{metrics['victim_count_mae']}**",
        "",
        "### Attribute detection (precision / recall / F1)",
        "",
        "| Attribute | Precision | Recall | F1 |",
        "|-----------|-----------|--------|-----|",
    ]
    for key, m in metrics["attributes"].items():
        lines.append(f"| {key} | {m['precision']} | {m['recall']} | {m['f1']} |")
    lines += [
        "",
        f"- Safe-message detection F1: **{metrics['safe_detection']['f1']}**",
        f"- Fake-SOS detection F1: **{metrics['fake_detection']['f1']}**",
    ]
    if llm_metrics:
        lines += [
            "",
            "## L1 + L3 (LLM) sample comparison",
            "",
            f"- LLM sample: {llm_metrics['calls']} reports, {llm_metrics['succeeded']} succeeded, {llm_metrics['elapsed_sec']}s",
            f"- Severity macro-F1: rules **{metrics['severity_macro_f1']}** vs rules+LLM **{llm_metrics['severity_macro_f1']}**",
            f"- Victim-count MAE: rules **{metrics['victim_count_mae']}** vs rules+LLM **{llm_metrics['victim_count_mae']}**",
            "",
            "| Attribute | Rules F1 | Rules+LLM F1 |",
            "|-----------|----------|--------------|",
        ]
        for key in metrics["attributes"]:
            lines.append(
                f"| {key} | {metrics['attributes'][key]['f1']} | {llm_metrics['attributes'][key]['f1']} |"
            )
        lines.append("")
        verdict = "AI justified" if llm_metrics["severity_macro_f1"] > metrics["severity_macro_f1"] + 0.01 else "AI NOT justified on severity (per KB file 12 §4)"
        lines.append(f"**AI decision rule:** {verdict}")
    lines += ["", "## Limitations", "", "- Synthetic labelled data generated from templates (ground truth by construction).",
              "- Human baseline pending (manual triage of a 200-report sample, timed).",
              "- LLM numbers are a sample; campus gateway latency affects throughput.", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()