# NETRA — Demo Strategy

> Mirrors KB file 21. **Show the decision improving, not the dashboard shining.**

## Interactive Segment — "Judges become victims" (added 2026-08-19)

**Access method 1 (primary): Cloudflare quick tunnel — no Wi-Fi/hotspot needed.**
```bash
/tmp/opencode/cloudflared tunnel --url http://localhost:5173
# prints a https://*.trycloudflare.com URL (random each launch)
```
Open that URL on the **projector** — it shows a QR code. Judges scan → their phone opens the same page → they tap a distress preset or type their own → **SEND SOS** → report flows through the real pipeline → zones form on the projector live.

- No account, no signup, **no interstitial page** (ngrok free tier shows a one-time "Confirm" page in browsers — cloudflared does not).
- One tunnel is enough: the victim page's API calls ride the same tunnel → Vite proxy → backend (`CORS=*`, `allowedHosts=true` already configured).
- Fallback if the laptop has no internet: **Access method 2** — `http://<laptop-ip>:5173/victim` on the same Wi-Fi (Vite runs `--host 0.0.0.0`).
- Fallback if neither works: scripted killer scenario from the sim panel (below).
- **Presenter route:** the dashboard at `/` is a clean monitoring screen (no sim controls). Append `/sim` (`…/sim`) to reveal the simulation panel + manual report console. Start the scenario there, then drop `/sim` and refresh for the clean view — the scenario keeps running in the backend.
- Re-download cloudflared if rebooted: `curl -sL -o /tmp/opencode/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 && chmod +x /tmp/opencode/cloudflared`

Details:
- Each phone = one independent source (`victim-xxxx` device id, random hotspot location ±250 m, `SMS/ERSS/WHATSAPP` source types) → feeds corroboration boost.
- The victim page uses its own isolated login (`citizen-sim / citizen-sim123`, role `CITIZEN`) so judges' phones never touch the dashboard session.
- Authz: `/events` accepts any active role; rate limit 120/min per user.
- **Fallback if the venue has no Wi-Fi/hotspot LAN:** skip the interactive segment and run the scripted killer scenario (below) from the sim panel at `…/sim` instead. The victim page also works on the presenter's own phone if the presenter hosts a hotspot.

Networking prerequisites (already configured):
- Vite runs with `-- --host 0.0.0.0` (LAN reachable); backend CORS relaxed to `*` (bearer-token auth, no cookies).
- Judges' phones and laptop on the same Wi-Fi; laptop firewall must allow 5173.

## Demo Principle

Do NOT demo "here's a map." Demo **the decision problem being solved**: signals → prioritized rescue zones → responder action. Everything runs locally; no dependency on live internet, government APIs, or external LLM (LLM degradation path rehearsed).

## The Killer Demo (flood scenario, deterministic seed 42)

### Minute 0
Dashboard: 0 incidents. Disaster context activated (Flood, District polygon, DEGRADED mode).

### Minute 2
50 reports arrive (multilingual, some duplicates, some noise). NETRA produces (settled, after live LLM enrichment; measured 2026-08-18 seed 42):

```text
50 reports → 17 incidents → 6 zones → 3 P1, 12 P2, 2 P4   (zones: 1 P1, 4 P2, 1 P4)
```

### Minute 4
30 more reports; one area now shows elderly + child + bleeding + rising water. Escalation as corroboration + LLM enrichment land:

```text
30 more → 22 incidents → 6 zones → 3 P1, 2 P2, 1 P3 zones (incidents: 7 P1, 13 P2, 1 P3, 1 P4)
```
Recommendation: 2 boats + medical response, with reasons.

### Minute 5
Field officer marks zone **RESCUED** → incident leaves active queue, remains in history.

### Punchlines
- priority ≠ report count (fewer victims but critical conditions ranks P1 over a larger safe zone)
- explainable priority reasons
- independent evidence count (84 messages ≠ 84 victims)
- uncertainty as confidence radius, not exact pins

## Adversarial Demos

1. **500 fake SOS from one location** → NETRA reduces confidence, flags anomaly (not "MASSIVE CRISIS")
2. **30 duplicates from one device** → counted as one source
3. **LLM killed mid-demo** → `NLP: LLM DEGRADED`, rules fallback continues, uncertain cases → human-review queue
4. **Network cut** → click `Net: cutout`; dashboard marks `CELLULAR_UNAVAILABLE` **and the behavior really changes**: the ingestion API rejects every non-SMS uplink (`ERSS`/`WHATSAPP`) with `UPLINK_UNAVAILABLE` (audited as `EVENT_REJECTED`) while **SMS reports keep landing** — judges see some phones fail and the SMS one succeed. `Net: degraded` adds real processing latency (0.3–0.8 s/event). This models loss of the upstream/cellular transport; it does not claim that a browser can stay connected after the laptop's own network adapter is physically disconnected.
5. **Backend restart** → state recovered, no critical data lost

## Deterministic Replay (NFR-097)

```text
T+00: 20 reports
T+05: 80 reports
T+10: building collapse report
T+15: field verification
```

Same input → same output. Seed 42. Prevents "the AI behaved differently during judging."

> Note: scenario timestamps replay as live (`now − 3h`) so the freshness component of the Rescue Priority Score behaves in demos; exact P1 counts depend on LLM enrichment completing (gateway-dependent latency). The counts above are the **settled** values once the queue drains.

## Recovery Script (NFR-098)

1. Backend crash → `docker compose up -d db` then `uvicorn app.main:app` → verify `/healthz` → refresh browser
2. LLM down → nothing to do; fallback automatic; verify status bar shows DEGRADED
3. Network cut → use the simulation `Net: cutout` control; local backend processing continues and map tiles fall back to the dark grid if external tiles are unavailable.
4. Browser refresh → all state from DB (no volatile state)

## What the Judge Should See

> "NETRA works because the system is under our control" — local, deterministic, recoverable.

## Golden Demo Rule

> Show the decision improving, not the dashboard shining.