"""TCET CoE AI Gateway client — OpenAI-compatible, Layer 3 enrichment only.

Hard timeouts + retry budget (docs/AI.md): LLM failure never blocks ingestion.
"""
import json
import time
from typing import Any

import httpx

from app.config import settings

SYSTEM_PROMPT = """You are an emergency-triage extraction engine for disaster response.
Extract structured fields from distress messages that may be multilingual (Hinglish/Hindi/English).
Return ONLY a JSON object with exactly these keys:
{"disaster":"FLOOD|EARTHQUAKE|CYCLONE|OTHER|UNKNOWN",
 "severity":"LOW|MEDIUM|HIGH|CRITICAL|UNKNOWN",
 "trapped":bool, "medical_critical":bool, "elderly":bool, "child":bool,
 "mobility_issue":bool, "pregnant":bool, "water_rising":bool,
 "victim_count":int|null, "access_issue":bool,
 "location_hint":string|null,
 "confidence":0.0-1.0}
No commentary, no markdown, only the JSON object."""

LLM_STATE = {"healthy": None, "last_check": None, "last_latency_ms": None, "last_error": None, "last_success": None, "sim_outage": False}


def set_sim_outage(on: bool) -> None:
    """Simulate an LLM-layer outage (demo): kill -> fast-fail all enrichment."""
    LLM_STATE["sim_outage"] = on
    if on:
        LLM_STATE.update({
            "healthy": False, "last_check": time.time(),
            "last_error": "simulated outage — LLM layer killed (rules-only mode)",
        })
    else:
        LLM_STATE.update({"healthy": None, "last_error": None, "last_check": time.time()})


def _endpoint() -> str:
    return f"{settings.ai_gateway_base_url.rstrip('/')}/chat/completions"


def extract_with_llm(text: str) -> dict[str, Any] | None:
    """Call the gateway; returns parsed extraction or None (never raises)."""
    if LLM_STATE.get("sim_outage"):
        LLM_STATE.update({"healthy": False, "last_check": time.time(),
                          "last_error": "simulated outage — LLM layer killed (rules-only mode)"})
        return None
    if not settings.llm_enabled or not settings.ai_gateway_api_key:
        LLM_STATE.update({"healthy": False, "last_error": "llm disabled or no key", "last_check": time.time()})
        return None

    payload = {
        "model": settings.ai_gateway_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
        "max_tokens": 300,
    }
    headers = {"Authorization": f"Bearer {settings.ai_gateway_api_key}", "Content-Type": "application/json"}

    start = time.time()
    for attempt in range(settings.llm_max_retries + 1):
        try:
            with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
                resp = client.post(_endpoint(), json=payload, headers=headers)
            latency_ms = int((time.time() - start) * 1000)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if "severity" not in parsed:
                    raise ValueError("missing severity key")
                LLM_STATE.update({
                    "healthy": True, "last_check": time.time(), "last_latency_ms": latency_ms,
                    "last_error": None, "last_success": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                parsed["confidence"] = _clamp_conf(parsed.get("confidence"))
                return parsed
            LLM_STATE["last_error"] = f"HTTP {resp.status_code}"
        except Exception as exc:  # timeout, connection, JSON errors
            LLM_STATE["last_error"] = f"{type(exc).__name__}: {str(exc)[:120]}"
        time.sleep(0.4 * (attempt + 1))

    LLM_STATE.update({"healthy": False, "last_check": time.time()})
    return None


def _clamp_conf(v: Any) -> float:
    try:
        return max(0.0, min(1.0, float(v)))
    except (TypeError, ValueError):
        return 0.5