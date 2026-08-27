# CrisisCore — Security Notes

## PII Stored Per Module

| Module | PII Field | Type | Risk |
|--------|-----------|------|------|
| **Auth/Users** | `phone` | Phone number (10-15 chars) | High — direct identifier |
| **Incidents** | `lat`, `lng` | Precise GPS coordinates | High — reveals victim location |
| **Incidents** | `photo_url` | URL to uploaded photo | Medium — may contain faces/locations |
| **Volunteers** | `lat`, `lng` | Last-known GPS position | Medium — tracks volunteer location |
| **Resources** | `lat`, `lng` | GPS coordinates of resource | Low — asset location, not personal |
| **Risk Zones** | `lat`, `lng` | Geographic center of risk area | Low — aggregate spatial data |
| **Notifications** | `recipient_id` | Foreign key to user | Medium — links to user identity |
| **Mesh Messages** | `origin_device_id` | Device identifier | Medium — can track device |

## Encryption & Transport

- **In transit:** TLS is required in production. The Docker Compose setup does NOT enable TLS by default (demo/dev mode). For deployment behind a reverse proxy (nginx/caddy), terminate TLS there.
- **At rest:** PostgreSQL does not encrypt at rest by default. For production, enable disk encryption or PostgreSQL TDE.
- **Passwords:** Hashed with bcrypt via `passlib`. Raw passwords are never stored or logged.
- **JWT tokens:** Signed with HS256. Token expiry is configurable via `JWT_EXPIRE_MINUTES` (default 1440 = 24h). Tokens contain only `user_id` and `role` — no PII.

## Recommendations for Production

1. **Phone numbers:** Store only hashed phone numbers for lookup, or use a separate encrypted column for display.
2. **GPS precision:** Round coordinates to ~3 decimal places (~111m precision) for incident locations to reduce re-identification risk.
3. **Photo URLs:** Use pre-signed, time-limited URLs. Never store raw photos on the same server.
4. **Audit log:** The `audit_log` table captures before/after state of entities — restrict access to admin role only.
5. **Rate limiting:** Add rate limiting on `/auth/login` and `/incidents` endpoints to prevent abuse.
6. **CORS:** In production, restrict `allow_origins` to specific frontend domains, not `*`.
