# CrisisCore

AI-powered early-warning platform for landslide/flood risk in a pilot NER district. Hackathon MVP built with FastAPI + PostGIS + Redis.

## Quick Start

```bash
docker compose up
```

That's it. API available at `http://localhost:8000`, docs at `http://localhost:8000/docs`.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `postgresql+asyncpg://crisiscore:crisiscore@db:5432/crisiscore` | Async SQLAlchemy connection string |
| `DATABASE_URL_SYNC` | No | `postgresql://crisiscore:crisiscore@db:5432/crisiscore` | Sync connection for Alembic |
| `REDIS_URL` | No | `redis://redis:6379/0` | Redis connection for queue + pub/sub |
| `JWT_SECRET` | No | `crisiscore-dev-secret-change-in-prod` | HMAC signing key for JWT tokens |
| `JWT_EXPIRE_MINUTES` | No | `1440` | Token lifetime in minutes |
| `NOTIFICATION_PROVIDER` | No | `console` | Provider: `console`, `twilio`, `fcm`, `ussd` |
| `TWILIO_ACCOUNT_SID` | No | *(empty)* | Twilio account SID (only if provider=twilio) |
| `TWILIO_AUTH_TOKEN` | No | *(empty)* | Twilio auth token |
| `TWILIO_FROM_NUMBER` | No | *(empty)* | Twilio sender number |
| `FCM_SERVER_KEY` | No | *(empty)* | Firebase Cloud Messaging key |
| `RISK_API_URL` | No | *(empty)* | External risk inference API URL |
| `AUTO_REASSIGN_MINUTES` | No | `5` | Minutes before auto-reassignment triggers |

When left unset, all optional variables default to demo-safe stub behavior.

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/health` | None | DB + Redis health check |
| `POST` | `/auth/register` | None | Register new user |
| `POST` | `/auth/login` | None | Login, get JWT |
| `POST` | `/incidents` | citizen+ | Create SOS incident |
| `GET` | `/incidents/{id}` | any | Get incident details |
| `PATCH` | `/incidents/{id}/verify` | officer+ | Verify incident |
| `GET` | `/incidents` | any | List/filter incidents |
| `POST` | `/incidents/sms` | None | SMS-style incident (feature phone) |
| `POST` | `/volunteers/heartbeat` | volunteer+ | Update volunteer position |
| `POST` | `/assignments` | officer+ | Create assignment |
| `PATCH` | `/assignments/{id}/status` | volunteer+ | Update assignment status |
| `POST` | `/resources` | any | Register resource |
| `GET` | `/resources/nearby` | any | Find nearby resources |
| `GET` | `/risk` | any | Get risk zones |
| `GET` | `/risk/{zone_id}/explain` | any | Explain risk factors |
| `GET` | `/notifications` | any | My notification history |
| `POST` | `/mesh/simulate` | any | Demo mesh relay |
| `GET` | `/status/{incident_id}` | any | Poll incident status |
| `WS` | `/ws/status` | None | Real-time status updates |

## Architecture

- **Single FastAPI app** — modular routers, no microservices overhead
- **PostgreSQL + PostGIS** — spatial queries for nearby resources and risk zones
- **Redis** — notification queue, WebSocket broadcast fan-out, matching queue
- **JWT + RBAC** — 4 roles: citizen, volunteer, officer, admin
- **Auto-reassign** — background job reassigns unacknowledged assignments after 5 min
- **Audit log** — every create/update to incidents, assignments, resources is logged

## Modules (Anjishnu Ghosh)

- **Notifications** — provider interface with console/twilio/fcm/ussd backends
- **Risk Integration** — wraps risk zones table, provides explainability endpoint
- **Resources** — CRUD + PostGIS spatial queries, wired into matching engine
- **Mesh Stub** — simulated store-and-forward relay for demo
- **Realtime** — WebSocket + Redis pub/sub for multi-worker broadcast
- **Failure Tests** — notification retry, auto-reassign dedup, WS reconnect

## Running Tests

```bash
# Inside the API container:
pytest tests/ -v

# Or from host (with test DB):
DATABASE_URL=postgresql+asyncpg://crisiscore:crisiscore@localhost:5432/crisiscore_test pytest tests/ -v
```

## Evidence Pack

- Git history shows phase-by-phase commits
- `tests/test_api.py` — full API flow tests
- `tests/test_notification_retry.py` — network-drop retry test
- `tests/test_auto_reassign.py` — deduplication test
- `tests/test_websocket.py` — reconnect correctness test
- `SECURITY_NOTES.md` — PII inventory and encryption notes
- Sample `/health` response:
  ```json
  {"status": "healthy", "timestamp": "2026-08-27T...", "checks": {"db": "ok", "redis": "ok", "notification_queue_depth": 0}}
  ```
