# NETRA — Database Schema

> Mirrors KB file 10 (Data Architecture). Core principle: **Raw evidence, derived intelligence, and human decisions must remain distinguishable.**

## Data Classes (never conflate)

| Class | Meaning | Example |
|-------|---------|---------|
| RAW | what was reported | citizen SMS text |
| DERIVED | what the system inferred | severity, vulnerability, confidence |
| SYSTEM | what the system decided | priority, recommendation |
| HUMAN | what a responder decided | override, verification, rescue |

## Entities

### disasters
```
id, name, type (FLOOD|EARTHQUAKE|CYCLONE|OTHER), affected_geography (geometry),
activation_time, severity_context, operating_mode, created_at
```

### events (raw, immutable — never deleted)
```
id, event_id (unique), disaster_id, source_type (SMS|ERSS|ELS|WHATSAPP|FIELD|MANUAL|SIMULATED),
source_timestamp, received_timestamp, text, source_identifier (pseudonymized),
location_lat, location_lon, location_accuracy_m, location_source, metadata (jsonb),
idempotency_key, processing_status (RECEIVED|PROCESSED|FAILED|UNRESOLVED), created_at
```

### evidence (source-linked, provenance preserved)
```
id, event_id, incident_id (nullable), source_type, timestamp, content_reference,
location_lat, location_lon, location_accuracy_m, extraction (jsonb: attributes+confidence+model),
confidence, relationship (PRIMARY|CORROBORATING|FIELD_VERIFIED), created_at
```

### incidents (consolidated representation)
```
id, incident_id (unique), disaster_id, status, location_lat, location_lon,
location_confidence, severity, victim_estimate, vulnerability (jsonb),
confidence, priority (P1..P4|UNRATED), zone_id (nullable), evidence_count,
independent_source_count, created_at, updated_at, last_evidence_at, resolved_at
```

### operational_zones
```
id, zone_id (unique), disaster_id, center_lat, center_lon, radius_m, incident_ids (jsonb),
evidence_count, independent_source_count, confidence, priority, status, updated_at
```

### priority_scores (versioned history)
```
id, incident_id, score, level (P1..P4), reasons (jsonb), rule_version, model_version, timestamp
```

### recommendations
```
id, incident_id, resources (jsonb), reasons (jsonb), rule_version,
status (SUGGESTED|ACCEPTED|REJECTED), created_at, resolved_at
```

### field_updates
```
id, incident_id, user_id, update_type (VERIFY|VICTIM_COUNT|ACCESS|MEDICAL|RESCUED|FALSE|NOTE),
values (jsonb), notes, timestamp, sync_state
```

### users / roles
```
id, username, password_hash, role (ADMIN|OPERATOR|COMMANDER|FIELD_RESPONDER|AUDITOR),
display_name, is_active, created_at
```

### audit_logs (append-only intent)
```
id, user_id, action, target_type, target_id, previous_value (jsonb),
new_value (jsonb), reason, timestamp
```

### model_versions / rule_versions
```
id, name, version, description, created_at, active
```

## Relationships

```text
Disaster 1───N Incidents
Incident 1───N Events (via evidence links)
Incident N───1 Zone
Incident 1───N PriorityScores (history, versioned)
Incident 1───N Recommendations
Incident 1───N FieldUpdates
Evidence 1───1 Event (provenance preserved)
```

## Spatial

- The prototype runs on the PostGIS Docker image, but the current SQLAlchemy schema stores coordinates as scalar latitude/longitude floats and performs haversine matching in Python.
- PostGIS geometry columns and GIST indexes remain a follow-up migration, not a current runtime capability.
- Uncertainty is stored as `location_accuracy_m` — never false precision.

## Time

- UTC internally, local timezone in UI
- `source_timestamp` (when event happened) ≠ `received_timestamp` (when NETRA got it) — required for degraded connectivity

## Versioning

- Every AI output: `{model: name, version, timestamp, confidence}` in evidence.extraction
- Every priority/recommendation: `rule_version` / `model_version`