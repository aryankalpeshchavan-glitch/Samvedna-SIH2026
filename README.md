# CrisisCore

AI-powered early-warning platform for landslide/flood risk in a pilot NER district. Hackathon MVP built with FastAPI + SQLAlchemy (async) + Redis.

## Quick Start

**Local dev (recommended, works out of the box):**

```bash
pip install -r requirements.txt
redis-server &          # or run Redis via any local instance/container
python run.py
```

API available at `http://localhost:8000`, docs at `http://localhost:8000/docs`. By default this uses a local SQLite file (`crisiscore.db`) — no extra setup needed.

**Docker Compose:**

```bash
docker compose up
```

> ⚠️ Not currently working end-to-end: `docker-compose.yml` targets Postgres and runs `alembic upgrade head`, but the repo has no `alembic/` migrations directory yet and `requirements.txt` doesn't include an async Postgres driver (`asyncpg`). Use the local dev path above until this is wired up, or add migrations + `asyncpg` to `requirements.txt` first.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite+aiosqlite:///./crisiscore.db` | Async SQLAlchemy connection string. Set to a Postgres URL (e.g. `postgresql+asyncpg://...`) to use Postgres instead — requires adding `asyncpg` to `requirements.txt` |
| `REDIS_URL` | No | `redis://localhost:6379/0` | Redis connection for queue + pub/sub |
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
- **SQLite by default (async SQLAlchemy)** — zero-setup local dev; swappable for Postgres via `DATABASE_URL`
- **No PostGIS/spatial index** — "nearby" queries (`/resources/nearby`, matching engine) fetch candidates and filter in Python with a haversine distance calculation, not a spatial index. Fine at hackathon scale; would need PostGIS or a spatial index for production scale
- **Redis** — notification queue, WebSocket broadcast fan-out, matching queue
- **JWT + RBAC** — 4 roles: citizen, volunteer, officer, admin
- **Auto-reassign** — background job reassigns unacknowledged assignments after 5 min
- **Audit log** — every create/update to incidents, assignments, resources is logged

## Modules (Anjishnu Ghosh)

- **Notifications** — provider interface with console/twilio/fcm/ussd backends
- **Risk Integration** — wraps risk zones table, provides explainability endpoint
- **Resources** — CRUD + haversine-based nearby queries, wired into matching engine
- **Mesh Stub** — simulated store-and-forward relay for demo
- **Realtime** — WebSocket + Redis pub/sub for multi-worker broadcast
- **Failure Tests** — notification retry, auto-reassign dedup, WS reconnect

## Running Tests

Most test files (`test_auto_reassign.py`, `test_notification_retry.py`, `test_websocket.py`) use whatever `DATABASE_URL` resolves to (SQLite by default), so they run with no extra setup:

```bash
pytest tests/ -v
```

`test_api.py` is the exception — it hardcodes a Postgres test DB (`postgresql+asyncpg://crisiscore:crisiscore@localhost:5432/crisiscore_test`) and needs the `asyncpg` driver installed plus a running Postgres instance with that DB created:

```bash
pip install asyncpg
# with a local Postgres running and crisiscore_test DB created:
pytest tests/test_api.py -v
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
