# NETRA — Security & Privacy Checklist

> Mirrors KB file 13. Security score target: 5/10 → 8/10.

## Data Classification

| Class | Example | Protection |
|-------|---------|-----------|
| PII | phone numbers, names | minimize, pseudonymize, encrypted storage |
| Precise location | victim coordinates | role-restricted access, confidence radius in public views |
| Medical/sensitive | medical emergencies, vulnerability | strictly authorized access, audit logs |
| Operational | incident state, priority | authorized responder access |
| Audit | who did what | append-only intent, protected from modification |

## Controls (MVP)

- [x] Authentication — no anonymous operational access (JWT)
- [x] RBAC — ADMIN / OPERATOR / COMMANDER / FIELD_RESPONDER / AUDITOR
- [x] Least privilege — permissions per role only
- [ ] HTTPS/TLS — behind local deployment; no plaintext app transport in prod
- [ ] Encryption at rest — sensitive fields; production policy
- [x] Audit logs — login, access, override, verification, field updates, ingestion
- [x] Input validation — text, coordinates, identifiers, payloads (Pydantic + bounds)
- [x] Rate limiting — /events (120/min), /auth (20/min), slowapi
- [x] Data minimization — only operational fields
- [ ] Retention — configurable, law-aligned (documented, not invented)
- [x] Sessions — JWT expiry + role checks per request
- [x] Fail-closed — invalid auth = denied; never anonymous fallback

## Fake-Report Defense

- Unique sources vs message count (independent_source_count)
- Spatial/temporal pattern analysis → coordinated fake-SOS detection
- Source reliability metadata (field > citizen)
- Anomaly flagging → surfaced to humans

## Secrets

- `.env` holds `AI_GATEWAY_API_KEY`, `JWT_SECRET`, DB URL
- `docs/ai-gateway.md` is gitignored (contains raw key)
- Never commit `.env`, keys, or logs with PII

## Logging Without PII Leakage (NFR-088)

- Redact phone numbers, names, precise victim details in logs
- Use pseudonymous source_identifier

## Offline Security (file 13 §7)

- Local auth still required
- Encrypted local storage intent
- Sync authenticated on reconnection

## Testing (MVP)

- [x] unauthorized access attempts → 401/403 (tests/test_security.py)
- [x] invalid authentication → fail closed
- [x] role escalation attempts → denied (audit endpoint 403 for OPERATOR)
- [x] injection attempts (SQL/text) → sanitized (Pydantic validation)
- [x] malformed payloads → structured VALIDATION_ERROR
- [x] rate limiting → 429 after burst (verified live + test)
- [x] no exposed secrets in repo/logs (.env + ai-gateway.md gitignored)

## Golden Security Rule

> Security failures fail closed. Emergency data access is never anonymous, never unlogged, and never retained longer than policy allows.