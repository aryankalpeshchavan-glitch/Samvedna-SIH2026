# Changelog

All notable changes to the CrisisCore Backend are documented in this file.

---

## [Day 5] — Reliability, Security & Observability Sprint
**Status:** Implementation Complete

### Added & Hardened
- **Data Freshness / Provenance:** Added `RISK_FRESHNESS_MINUTES` to configurable settings. Decision and Risk endpoints now strictly evaluate the age of risk models against this threshold, transitioning outdated records to a `stale` data status.
- **Controlled Failure Handling:** Risk API and Intelligence Decision layers now gracefully return HTTP 503 instead of fabricating false `0.5` risk scores when models are unavailable or unpopulated.
- **Security Audit:** Validated `auth.py` handles token expiry and malformed JWTs robustly. Cleaned `.env.example` of secrets. Verified RBAC rules correctly lock down operations.
- **Idempotency & State Protection:** Verified existing state machine securely handles duplicate Volunteer ACKs and assignment completions via idempotent checks. Invalid state transitions properly raise 400s.
- **Safe Error Responses:** Introduced global generic `Exception` handler to `main.py` ensuring unexpected server faults yield standardized 500 JSON without exposing internal stack traces or SQL details.
- **Audit Logging Enhancement:** Masked sensitive fields (like passwords/tokens) in the central audit `_model_to_dict` serialization for safe provenance logging of entities.

---

## [Day 4] — Intelligence & Operational Decision Layer
**Commit:** `1d0f500`

### Added
- **Operational Priority Engine (`app/intelligence/priority.py`):**
  - Linear, explainable composite formula combining Risk (0.35), Exposure (0.30), Vulnerability (0.20), and Response Capacity Gap (0.15) into a normalized $0 \to 100$ priority score.
  - Triage categorization: `CRITICAL` ($\ge 80$), `HIGH` ($\ge 60$), `MEDIUM` ($\ge 40$), `LOW` ($< 40$).
- **Exposure Model & Storage (`app/models/exposure.py`):**
  - `ExposureZone` table capturing population, households, schools, hospitals, critical roads, hospital distance, early-warning capabilities, and road access quality.
  - Granular provenance tagging (`live`, `simulated`, `replayed`, `stale`) with explicit source attribution.
- **Driver Explanation Layer (`app/intelligence/explanation.py`):**
  - Translation of model driver keys (`rainfall_24h`, `rainfall_7day`, `slope`, `soil_moisture`, `ndvi`, etc.) to human-readable labels, descriptions, and units with safe fallback for unknown keys.
- **Action Recommendations Engine (`app/intelligence/actions.py`):**
  - Deterministic civil defense recommendation generator producing tailored advisories (DDMA alert, evacuation planning, road access restriction, hospital readiness, school precautions, mutual aid requests).
- **Intelligence Router (`app/routers/intelligence.py`):**
  - `POST /intelligence/decision` — Unified coordinate-based decision endpoint.
  - `GET /intelligence/decision/{zone_id}` — Zone-based decision endpoint.
  - `POST /intelligence/whatif` — Scenario simulator strictly labelled `"SIMULATION — NOT A FORECAST"`.
  - `POST /intelligence/exposure`, `GET /intelligence/exposure`, `GET /intelligence/exposure/nearby` — Exposure zone management.
- **Test Suite:**
  - 29 new tests in `tests/test_day4_intelligence.py` covering unit priority math, driver mappings, deterministic action rules, and integration endpoints.

---

## [Day 3] — Incident Response Lifecycle & Hardening
**Commit:** `ace1ba7` / `6536bf4`

### Added
- **Complete End-to-End Operational Lifecycle:**
  - Citizen SOS submission $\to$ Officer verification $\to$ Redis queue $\to$ Async matching $\to$ Volunteer assignment $\to$ Notification dispatch $\to$ Volunteer ACK $\to$ Completion.
- **Verification & Rejection Guards:**
  - `POST /incidents/{id}/verify` and `POST /incidents/{id}/reject` endpoints with strict role-based authorization (`officer`, `admin`).
- **Asynchronous Matching Worker (`app/background/matching_worker.py`):**
  - Worker consuming `matching_queue` from Redis, executing multi-factor matching (proximity + skill compatibility + nearby resources), and creating assignments with configurable SLA deadlines.
- **Auto-Reassignment Hardening (`app/background/auto_reassign.py`):**
  - Configurable SLA timeout (`ASSIGNMENT_ACK_TIMEOUT_SECONDS`) transitioning unacknowledged assignments to `timed_out` and reallocating to alternative volunteers.
- **Immutable Audit Logging (`app/core/audit_logger.py`):**
  - Automatic audit records on incident state transitions, assignment creation, volunteer ACK, and status modifications.
- **Integration Tests:**
  - `tests/test_day3_integration.py`, `tests/test_happy_path.py`, `tests/test_audit_lifecycle.py`.

---

## [Day 2] — Ingestion, Offline Sync & Redis Queue
**Commit:** `9dcca1c` / `6502077`

### Added
- **Offline Incident Sync (`POST /incidents/sync`):**
  - Idempotent batch ingestion for offline-captured incidents preserving client timestamps and preventing duplicate entries.
- **Redis Matching Queue Integration:**
  - Decoupled incident verification from matching via Redis list queues.
- **Real-Time WebSockets:**
  - `/ws/status` connection for streaming real-time status updates via Redis Pub/Sub.

---

## [Day 1] — Core Backend Foundation
**Commit:** `4b3b617`

### Added
- **FastAPI Core Foundation:**
  - Async SQLAlchemy ORM, JWT authentication, and 4-tier RBAC (`citizen`, `volunteer`, `officer`, `admin`).
  - Baseline CRUD for incidents, volunteers, assignments, and emergency resources.
  - Multi-provider notification abstraction (Console, Twilio, FCM).
