# NETRA — API Contract

> Mirrors KB file 11 (API Architecture). Base path: `/api/v1`. All responder APIs require auth. Errors are structured, never stack traces.

## Authentication

```
POST /api/v1/auth/login        {username, password} → {access_token, user}
GET  /api/v1/auth/me           → current user + role
POST /api/v1/auth/logout       (client discards token)
```

Roles: `ADMIN`, `OPERATOR`, `COMMANDER`, `FIELD_RESPONDER`, `AUDITOR`.

## Events

```
POST /api/v1/events            ingest emergency evidence (idempotent)
GET  /api/v1/events/{event_id} event + processing status
```

```jsonc
// POST /events
{
  "source_type": "SMS",                    // SMS | ERSS | ELS | WHATSAPP | FIELD | MANUAL | SIMULATED
  "source_timestamp": "2026-08-18T09:12:00Z",
  "text": "Paani kamar tak aa gaya hai, dadi chal nahi sakti",
  "location": {"lat": 19.0760, "lon": 72.8777, "accuracy_m": 50},
  "source_identifier": "device-7f3a",       // pseudonymized
  "idempotency_key": "sms-001"
}
```

```jsonc
// Response: rules/fusion run synchronously; LLM enrichment may remain queued.
{"event_id": "EVT-00001", "status": "PROCESSED", "incident_id": "INC-00001"}
```

## Incidents

```
GET    /api/v1/incidents          ?priority=&status=&disaster_id=&freshness=&limit=&offset=
GET    /api/v1/incidents/{id}     full detail: location, confidence, victims, severity,
                                  vulnerability, evidence, timeline, priority, recommendation

Incidents are currently created by event ingestion or simulation. Direct manual incident
creation and generic PATCH updates are not part of the prototype API; use field updates
for human verification/status changes.
```

## Evidence

```
GET /api/v1/incidents/{id}/evidence   all linked evidence with provenance
```

## Priority

```
GET  /api/v1/incidents/{id}/priority          current score + reasons + version
POST /api/v1/incidents/{id}/priority/override {priority, reason}   (COMMANDER+; audited)
```

## Zones

```
GET /api/v1/zones        ?disaster_id=&priority=&limit=
GET /api/v1/zones/{id}   zone geometry, incidents, confidence, priority
```

## Field Updates

```
POST /api/v1/incidents/{id}/field-updates   {update_type, values, notes}  (FIELD_RESPONDER+)
GET  /api/v1/incidents/{id}/field-updates
```

May trigger priority recalculation (FR-033).

## Recommendations

```
GET /api/v1/incidents/{id}/recommendation          current suggestion + reasons
POST /api/v1/incidents/{id}/recommendation/decision  {status: ACCEPTED|REJECTED} (OPERATOR+)
```

## Simulation (demo only, ADMIN/COMMANDER)

```
POST /api/v1/sim/disaster          activate disaster context {name, type, polygon, mode}
POST /api/v1/sim/reset             wipe operational tables → fresh demo state (worker stop/join)
POST /api/v1/sim/scenario/start    {scenario_id, seed}  → deterministic replay
POST /api/v1/sim/scenario/step     advance timeline
POST /api/v1/sim/inject            inject N reports (burst / fake-SOS / dupes)
POST /api/v1/sim/network           set connectivity state (NORMAL|DEGRADED|SEVERELY_DEGRADED|CELLULAR_UNAVAILABLE)
POST /api/v1/sim/llm               {enabled: bool} — kill/restore LLM layer (rules-only fallback)
```

## System / Dashboard

```
GET /healthz                  database health + configured NLP/LLM versions
GET /api/v1/system/status     connectivity state + source health + LLM health (NFR-017/099)
GET /api/v1/map-data          heat points + zones + incidents for the tactical map
GET /api/v1/audit             audit log (AUDITOR/ADMIN)
```

## Errors

```jsonc
{"detail": {"code": "CONFLICT", "message": "No scenario started"}}
```

Codes: `VALIDATION_ERROR`, `AUTHENTICATION_ERROR`, `AUTHORIZATION_ERROR`, `DEPENDENCY_FAILURE`, `MODEL_FAILURE`, `DATABASE_FAILURE`, `NETWORK_FAILURE`, `TIMEOUT`, `CONFLICT`, `UNKNOWN` (NFR-053).

## Idempotency

Events carry `idempotency_key`; re-submission returns the existing `event_id` without creating a duplicate (NFR-010).

## Golden API Rule

> The API must preserve the distinction between raw evidence, system-derived intelligence, and human-verified decisions. RAW EVENT → SYSTEM INTELLIGENCE → HUMAN DECISION.