# CrisisCore Backend — Frontend Integration Guide

This document defines the verified HTTP and WebSocket API contracts for the CrisisCore frontend application. All schemas, parameters, and response structures correspond directly to the active FastAPI backend implementation on branch `AJ-backend-work`.

---

## 1. Global Standards & Conventions

### Base URL & Protocol
* **Local Development:** `http://localhost:8000`
* **Interactive OpenAPI Documentation:** `http://localhost:8000/docs`
* **WebSocket Endpoint:** `ws://localhost:8000/ws/status`

### Authentication & Headers
All authenticated endpoints require an `Authorization` header containing the JWT Bearer token:
```http
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

### Roles & RBAC Hierarchy
* `citizen`: Can submit incidents, query risk and decision intelligence, view own incident statuses.
* `volunteer`: Can send GPS heartbeats (`/volunteers/heartbeat`), view assigned tasks (`/assignments/my`), and acknowledge/update assignment status.
* `officer`: Can verify/reject emergency incidents, manually create volunteer assignments, register exposure zones, and run what-if simulations.
* `admin`: Complete administrative oversight, full entity access, and audit log inspection.

### Data Provenance Labels
Every risk, exposure, decision, and scenario endpoint includes an explicit `data_status` field:
* `"live"`: Real-time sensor feed or validated field report.
* `"simulated"`: Synthetic data generated for demonstration or what-if scenario exploration.
* `"replayed"`: Historical sensor records replayed for testing.
* `"stale"`: Telemetry older than `RISK_FRESHNESS_MINUTES` (default: 60 minutes).
* `"unavailable"`: Service degraded / model output missing (HTTP 503).

> **Frontend Display Rule:** The frontend UI **must prominently display the provenance tag**. Simulated data or What-If projections must **never** be styled as live emergency forecasts.

---

## 2. Risk Intelligence Endpoints

### `GET /risk`
* **Auth:** Required (Any authenticated role)
* **Query Parameters:**
  * `bbox` (optional string): Bounding box `"south,west,north,east"` (e.g. `"25.5,90.5,27.0,92.5"`)
  * `horizon` (optional string, default: `"24h"`): Forecast horizon (e.g. `"12h"`, `"24h"`, `"48h"`, `"7d"`)
* **Response:** `200 OK` — `Array<RiskZoneOut>`
```json
[
  {
    "id": "zone-guwahati-east-01",
    "risk_score": 0.82,
    "horizon_hours": 24,
    "top_features": {
      "rainfall_24h": 185.4,
      "slope": 42.1,
      "soil_moisture": 0.88
    },
    "data_label": "live",
    "computed_at": "2026-08-31T12:00:00Z",
    "lat": 26.15,
    "lng": 91.75
  }
]
```

### `POST /risk` (ML Contract Endpoint)
* **Auth:** Required (`officer`, `admin`)
* **Request Body:**
```json
{
  "lat": 26.15,
  "lng": 91.75,
  "horizon_hours": 24,
  "features": {
    "rainfall_24h": 185.4,
    "slope": 42.1,
    "soil_moisture": 0.88
  }
}
```
* **Response:** `200 OK`
```json
{
  "risk_score": 0.82,
  "risk_level": "HIGH",
  "confidence": 0.84,
  "drivers": ["rainfall_24h", "slope", "soil_moisture"],
  "data_status": "live"
}
```
* **Error Response:** `503 Service Unavailable` if no risk zone data exists for the coordinates.

### `GET /risk/{zone_id}/explain`
* **Auth:** Required (Any authenticated role)
* **Response:** `200 OK`
```json
{
  "zone_id": "zone-guwahati-east-01",
  "risk_score": 0.82,
  "top_features": {
    "rainfall_24h": 185.4,
    "slope": 42.1
  },
  "explanation": "Top risk factors: rainfall_24h (impact: 185.400), slope (impact: 42.100)"
}
```

---

## 3. Operational Intelligence & Decision Endpoints

### `POST /intelligence/decision` (Primary Command Center View)
Answers: *Why is this location critical? What action should authorities take?*
* **Auth:** Required (Any authenticated role)
* **Request Body:**
```json
{
  "lat": 26.15,
  "lng": 91.75,
  "location_id": "loc-guwahati-01",
  "zone_id": "zone-guwahati-east-01"
}
```
*(Note: `zone_id` and `location_id` are optional; if omitted, backend queries the closest risk zone).*
* **Response:** `200 OK`
```json
{
  "location_id": "zone-guwahati-east-01",
  "lat": 26.15,
  "lng": 91.75,
  "risk": {
    "risk_score": 0.82,
    "risk_level": "HIGH",
    "confidence": 0.84,
    "drivers": ["rainfall_24h", "slope", "soil_moisture"],
    "data_status": "live"
  },
  "explanation": [
    {
      "key": "rainfall_24h",
      "label": "24-hour Rainfall",
      "description": "Total precipitation recorded over the last 24 hours.",
      "unit": "mm",
      "category": "Hydrology",
      "value": 185.4
    },
    {
      "key": "slope",
      "label": "Terrain Slope",
      "description": "Topographic inclination of the hillside terrain.",
      "unit": "degrees",
      "category": "Terrain",
      "value": 42.1
    }
  ],
  "exposure": {
    "population": 3400,
    "households": 850,
    "schools": 2,
    "hospitals": 1,
    "critical_roads": 2,
    "data_status": "live",
    "source": "State Disaster Management Authority GIS"
  },
  "priority": {
    "priority_score": 84.5,
    "priority_level": "CRITICAL",
    "weights": {
      "risk": 0.35,
      "exposure": 0.30,
      "vulnerability": 0.20,
      "response_gap": 0.15
    },
    "factors": {
      "risk": 0.82,
      "exposure": 0.76,
      "vulnerability": 0.80,
      "response_gap": 1.0
    }
  },
  "actions": [
    "Issue immediate DDMA Red Alert to local administration",
    "Pre-stage evacuation transport for vulnerable settlements",
    "Restrict vehicular movement along vulnerable road links",
    "Alert nearest hospital emergency department for triage readiness"
  ],
  "data_status": "live",
  "computed_at": "2026-08-31T12:00:00Z"
}
```

### `GET /intelligence/decision/{zone_id}`
* **Auth:** Required (Any authenticated role)
* **Response:** Identical schema to `POST /intelligence/decision`.

### `POST /intelligence/whatif` (Scenario Simulator)
* **Auth:** Required (`officer`, `admin`)
* **Request Body:**
```json
{
  "lat": 26.15,
  "lng": 91.75,
  "scenario_rainfall_mm": 250.0,
  "zone_id": "zone-guwahati-east-01"
}
```
* **Response:** `200 OK`
```json
{
  "scenario_label": "SIMULATION — NOT A FORECAST",
  "current_risk_score": 0.45,
  "projected_risk_score": 0.75,
  "current_priority_level": "MEDIUM",
  "projected_priority_level": "HIGH",
  "current_actions": [
    "Increase telemetry check frequency"
  ],
  "projected_actions": [
    "Issue DDMA Level 2 alert",
    "Pre-stage emergency response teams",
    "Issue early warning advisory to low-lying communities"
  ],
  "data_status": "simulated"
}
```

### `POST /intelligence/exposure`
* **Auth:** Required (`officer`, `admin`)
* **Request Body:**
```json
{
  "name": "Guwahati East Hill Settlement",
  "lat": 26.15,
  "lng": 91.75,
  "radius_km": 5.0,
  "population": 3400,
  "households": 850,
  "schools": 2,
  "hospitals": 1,
  "critical_roads": 2,
  "distance_to_hospital_km": 8.5,
  "has_early_warning": true,
  "road_access_quality": "moderate",
  "data_status": "live",
  "source": "MDoNER District Exposure Database"
}
```
* **Response:** `201 Created`

### `GET /intelligence/exposure` & `GET /intelligence/exposure/nearby`
* **Auth:** Required (Any authenticated role)
* **Nearby Query:** `GET /intelligence/exposure/nearby?lat=26.15&lng=91.75&radius_km=10.0`
* **Response:** `200 OK` — `Array<ExposureOut>`

---

## 4. Emergency Incident & Dispatch Endpoints

### `POST /incidents` (Citizen SOS Submission)
* **Auth:** Required (`citizen`, `volunteer`, `officer`, `admin`)
* **Request Body:**
```json
{
  "type": "landslide",
  "description": "Massive rockfall blocking NH-27 near Sonapur",
  "lat": 26.15,
  "lng": 91.75,
  "severity": 4,
  "photo_url": "https://example.com/incident-photo.jpg",
  "idempotency_key": "sos-client-uuid-98124"
}
```
* **Response:** `201 Created`
```json
{
  "id": "inc-0a9b8c7d-...",
  "reporter_id": 1,
  "type": "landslide",
  "description": "Massive rockfall blocking NH-27 near Sonapur",
  "lat": 26.15,
  "lng": 91.75,
  "severity": 4,
  "status": "reported",
  "data_label": "synthetic",
  "occurred_at": "2026-08-31T12:00:00Z",
  "created_at": "2026-08-31T12:00:00Z"
}
```

### `POST /incidents/{incident_id}/verify` (or `PATCH /incidents/{incident_id}/verify`)
* **Auth:** Required (`officer`, `admin`)
* **Request Body:**
```json
{
  "data_label": "live"
}
```
* **Response:** `200 OK` (Status updated to `"verified"`, enqueued to Redis matching queue).

### `POST /incidents/{incident_id}/reject` (or `PATCH /incidents/{incident_id}/reject`)
* **Auth:** Required (`officer`, `admin`)
* **Response:** `200 OK` (Status updated to `"rejected"`).

### `POST /incidents/sync` (Offline Incident Batch Synchronization)
* **Auth:** Required (`citizen`, `volunteer`, `officer`, `admin`)
* **Request Body:**
```json
{
  "items": [
    {
      "type": "landslide",
      "description": "Offline captured report",
      "lat": 26.15,
      "lng": 91.75,
      "severity": 3,
      "idempotency_key": "offline-client-report-01",
      "occurred_at": "2026-08-31T10:30:00Z"
    }
  ]
}
```
* **Response:** `200 OK`
```json
{
  "synced_count": 1,
  "duplicate_count": 0,
  "error_count": 0,
  "synced": [...],
  "duplicates": [],
  "errors": []
}
```

---

## 5. Responder & Assignment Endpoints

### `POST /volunteers/heartbeat`
* **Auth:** Required (`volunteer`, `officer`, `admin`)
* **Request Body:**
```json
{
  "lat": 26.155,
  "lng": 91.752,
  "availability_status": "available",
  "skills": ["first_aid", "search_and_rescue", "heavy_machinery"]
}
```
* **Response:** `200 OK`

### `GET /assignments/my`
* **Auth:** Required (`volunteer`, `officer`, `admin`)
* **Response:** `200 OK` — `Array<AssignmentOut>` for current volunteer.

### `POST /assignments/{assignment_id}/ack` (or `PATCH /assignments/{assignment_id}/status`)
* **Auth:** Required (Assigned `volunteer`, `officer`, `admin`)
* **Convenience Endpoint:** `POST /assignments/{id}/ack` acknowledges assignment.
* **Status Update Endpoint:** `PATCH /assignments/{id}/status` with body:
```json
{
  "status": "acked"
}
```
*(Valid transitions: `pending` $\to$ `acked` $\to$ `in_progress` $\to$ `done`)*.
* When marked `"done"`, parent incident automatically transitions to `"resolved"`.

---

## 6. Real-Time Status & WebSockets

### `WS /ws/status`
* **Protocol:** `WebSocket`
* **Purpose:** Real-time push notifications of verified incidents, assignment updates, and status changes.
* **Message Format:**
```json
{
  "event": "incident_verified",
  "incident_id": "inc-0a9b8c7d-...",
  "status": "verified",
  "lat": 26.15,
  "lng": 91.75,
  "severity": 4,
  "timestamp": "2026-08-31T12:00:00Z"
}
```

---

## 7. Standard Error Handling

| HTTP Status | Error Detail Format | Trigger Condition |
|---|---|---|
| `400 Bad Request` | `{"detail": "Invalid state transition..."}` | Illegal assignment transition, bad parameters |
| `401 Unauthorized` | `{"detail": "Could not validate credentials"}` | Missing, expired, or malformed JWT token |
| `403 Forbidden` | `{"detail": "Operation not permitted"}` | Role insufficient for requested operation |
| `404 Not Found` | `{"detail": "Resource not found"}` | Invalid incident ID, zone ID, or assignment ID |
| `503 Service Unavailable` | `{"detail": "Risk service unavailable...", "error_code": "RISK_SERVICE_UNAVAILABLE"}` | ML model missing / no risk data for coordinates |
| `500 Internal Server Error` | `{"detail": "Internal server error", "error_code": "INTERNAL_ERROR"}` | Unhandled server exception (stack trace sanitized) |
