# CrisisCore — Security Notes

## PII & Sensitive Attributes Stored Per Module

| Module | Sensitive Field | Type | Risk Level | Protection / Sanitization |
|---|---|---|---|---|
| **Auth/Users** | `phone` | Phone number (10-15 chars) | High — Direct Identifier | Stored hashed or restricted to admin roles. |
| **Auth/Users** | `hashed_password` | Bcrypt hash | Critical | Never logged or returned in user responses. |
| **Incidents** | `lat`, `lng` | GPS coordinates | High — Victim Location | Guarded by RBAC; sanitized on aggregate exports. |
| **Incidents** | `photo_url` | URL to uploaded image | Medium — Visual context | Restricted access. |
| **Volunteers** | `lat`, `lng` | Last-known GPS position | Medium — Tracking location | Accessible only for dispatch and officer triage. |
| **Resources** | `lat`, `lng` | GPS coordinates of resource | Low — Asset location | Public safety asset tracking. |
| **Risk Zones** | `lat`, `lng` | Spatial centroid of risk area | Low — Aggregate data | Geospatial bounding. |
| **Notifications** | `recipient_id` | Foreign key to user | Medium — Links to identity | Redacted in public responses. |
| **Mesh Messages** | `origin_device_id` | Device identifier | Medium — Device tracking | Mesh relay routing metadata. |

---

## Encryption, Transport & Storage

- **In Transit:** TLS is required in production. For deployment behind a reverse proxy (Nginx, Caddy, Cloudflare), terminate TLS at the ingress.
- **At Rest:** Database disk encryption (LUKS or PostgreSQL TDE) should be enabled in production environments.
- **Passwords:** Hashed with bcrypt via `passlib`. Raw passwords are never stored or logged in plain text.
- **JWT Tokens:** Signed with HMAC-SHA256 (`HS256`). Configurable expiry via `JWT_EXPIRE_MINUTES` (default: 1440 min = 24h). Tokens carry only `user_id` and `role` claims — no PII.

---

## Day 5 Security & Reliability Hardening

1. **Audit Log Credential Redaction:** The central audit logger (`app/core/audit_logger.py`) automatically strips sensitive keys (`password_hash`, `token`, `secret`, `api_key`, `jwt`) during entity delta serialization, ensuring credentials never leak into the `audit_logs` table.
2. **Sanitized Error Responses:** A global exception handler in `app/main.py` catches unhandled runtime faults and returns standard sanitized JSON (`{"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}`), preventing internal stack traces or SQL errors from being exposed to clients.
3. **Data Freshness / TTL Enforcement:** The backend enforces `RISK_FRESHNESS_MINUTES` on risk intelligence models to prevent outdated predictions from being treated as active field data.
4. **Controlled Service Degradation:** Returns explicit HTTP 503 (`RISK_SERVICE_UNAVAILABLE`) when model outputs are missing rather than fabricating false default values.

---

## Recommendations for Production Deployment

1. **JWT Secrets:** In production, generate a high-entropy secret via `openssl rand -hex 32` and provide via secure secret managers (e.g. AWS Secrets Manager, Vault).
2. **CORS:** Restrict `allow_origins` in `app/main.py` from `*` to verified frontend domain names.
3. **Rate Limiting:** Place an API gateway (e.g. Nginx, Cloudflare, AWS WAF) in front of `/auth/login` and `/incidents` endpoints to mitigate brute-force and DoS attacks.
