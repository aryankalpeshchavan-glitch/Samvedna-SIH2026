# Changelog

All notable changes to the CrisisCore Backend are documented in this file.

---

## [Day 5] — Reliability, Security & Observability Sprint
**Commit:** `1474060`
**Test Suite:** 68/68 PASSED

### Added & Hardened
- **Data Freshness / Provenance Tracking:**
  - Integrated `RISK_FRESHNESS_MINUTES` configuration parameter (default: 60 minutes).
  - Decision and Risk endpoints (`/intelligence/decision`, `/risk`) strictly validate the age of stored `RiskZone` models against `computed_at`, transitioning outdated records to a `stale` provenance status.
- **Controlled Failure Handling & Safe Degradation:**
  - Intelligence and Risk endpoints gracefully respond with HTTP 503 (`RISK_SERVICE_UNAVAILABLE`) when hazard data is missing rather than fabricating false default risk scores.
- **Safe Global Error Handling:**
  - Implemented centralized exception handler in `app/main.py` converting unhandled server exceptions into sanitized JSON responses (`{"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}`) preventing stack trace or SQL leakage to clients.
- **Audit Logging Security Hardening:**
  - Added sensitive field blacklisting (`password_hash`, `token`, `secret`, `api_key`, `jwt`) to `app/core/audit_logger.py` serialization routines to prevent credential leakage into audit records.
- **Authentication & RBAC Edge Case Hardening:**
  - Added comprehensive test coverage in `tests/test_day5_reliability.py` verifying behavior on expired tokens, invalid signatures, missing bearer headers, and unauthorized role escalations.
- **Idempotency & State Safety:**
  - Verified state machine idempotency across duplicate volunteer ACKs, repeated completions, and invalid lifecycle transitions.

---

## [Day 4] — Intelligence & Operational Decision Layer
**Commit:** `1d0f500`
**Test Suite:** 61/61 PASSED

### Added
- **Operational Priority Engine (`app/intelligence/priority.py`):**
  - Deterministic composite formula combining Risk (0.35), Exposure (0.30), Vulnerability (0.20), and Response Capacity Gap (0.15) into a normalized $0 \to 100$ priority score.
  - Operational triage categorization: `CRITICAL` ($\ge 80$), `HIGH` ($\ge 60$), `MEDIUM` ($\ge 40$), `LOW` ($< 40$).
- **Exposure Model & Storage (`app/models/exposure.py`):**
  - `ExposureZone` table capturing population, households, schools, hospitals, critical roads, distance to medical centers, early-warning capabilities, and road access quality.
  - Multi-status data provenance tagging (`live`, `simulated`, `replayed`, `stale`) with explicit source attribution.
- **Driver Explanation Layer (`app/intelligence/explanation.py`):**
  - Human-readable translation of ML feature keys (`rainfall_24h`, `rainfall_7day`, `slope`, `soil_moisture`, `ndvi`, etc.) with physical units, hazard categories, and safe fallbacks for unmapped drivers.
- **Action Recommendations Engine (`app/intelligence/actions.py`):**
  - Deterministic civil defense recommendation generator producing tailored advisories (DDMA alerts, evacuation staging, road access controls, medical preparedness, school closures, inter-district mutual aid).
- **Intelligence Router (`app/routers/intelligence.py`):**
  - `POST /intelligence/decision` — Coordinate-based unified decision endpoint.
  - `GET /intelligence/decision/{zone_id}` — Zone-based decision endpoint.
  - `POST /intelligence/whatif` — Scenario simulator strictly labelled `"SIMULATION — NOT A FORECAST"`.
  - `POST /intelligence/exposure`, `GET /intelligence/exposure`, `GET /intelligence/exposure/nearby` — Exposure zone management endpoints.
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
