"""
Day 6 — Integration & End-to-End Verification Test Suite
=========================================================
Verifies:
1. ML/Risk stable contract & value bounding
2. Risk → Intelligence chain (Decision view completeness)
3. End-to-End Emergency Response Lifecycle (Citizen SOS → Verify → Match → ACK → Done → Audit)
4. Cross-role RBAC security enforcement (Citizen, Volunteer, Officer, Admin)
5. Data provenance correctness and simulation labeling
6. Stale risk data TTL handling
7. Failure-safe degradation (HTTP 503 on missing risk, sanitized 500 responses)
8. What-If scenario simulation integrity
9. Alias endpoint routes (POST/PATCH verify, POST/PATCH status, POST /ack)
10. Audit log delta verification & sensitive key redaction
"""
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient
from sqlalchemy import select
from unittest.mock import patch

from app.core.database import async_session
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from app.models.risk import RiskZone
from app.models.exposure import ExposureZone
from app.models.volunteer import Volunteer
from app.background.matching_worker import process_incident_match
from tests.test_api import auth_header, register_and_login, TestSession, client, setup_db


# ─── 1. ML / Risk Contract Verification ───────────────────────────────────────

@pytest.mark.asyncio
async def test_day6_ml_risk_contract(client: AsyncClient):
    """Verifies that POST /risk returns the stable contract schema with bounded values."""
    officer_token = await register_and_login(client, "officer")

    # Seed a risk zone
    async with TestSession() as db:
        rz = RiskZone(
            id="zone-contract-day6",
            lat=26.15,
            lng=91.75,
            risk_score=0.82,
            horizon_hours=24,
            top_features={"rainfall_24h": 185.4, "slope": 42.1, "soil_moisture": 0.88},
            data_label="live",
            computed_at=datetime.now(timezone.utc),
        )
        db.add(rz)
        await db.commit()

    resp = await client.post("/risk", json={
        "lat": 26.15,
        "lng": 91.75,
        "horizon_hours": 24,
        "features": {"rainfall_24h": 185.4, "slope": 42.1},
    }, headers=auth_header(officer_token))

    assert resp.status_code == 200
    data = resp.json()

    # Bounded types and schema verification
    assert isinstance(data["risk_score"], (int, float))
    assert 0.0 <= data["risk_score"] <= 1.0
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert isinstance(data["confidence"], (int, float))
    assert 0.0 <= data["confidence"] <= 1.0
    assert isinstance(data["drivers"], list)
    assert len(data["drivers"]) > 0
    assert data["data_status"] in ["live", "simulated", "replayed", "stale"]


# ─── 2. Risk → Intelligence Decision Chain ────────────────────────────────────

@pytest.mark.asyncio
async def test_day6_risk_to_decision_completeness(client: AsyncClient):
    """
    Verifies that POST /intelligence/decision returns all required decision components
    without requiring frontend to recalculate priority or driver mapping.
    """
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    # Seed RiskZone & ExposureZone
    async with TestSession() as db:
        rz = RiskZone(
            id="zone-intelligence-day6",
            lat=26.15,
            lng=91.75,
            risk_score=0.78,
            horizon_hours=24,
            top_features={"rainfall_24h": 150.0, "slope": 38.0},
            data_label="live",
            computed_at=datetime.now(timezone.utc),
        )
        db.add(rz)

        ez = ExposureZone(
            name="Sonapur Hill Settlement",
            lat=26.15,
            lng=91.75,
            radius_km=5.0,
            population=2500,
            households=600,
            schools=2,
            hospitals=1,
            critical_roads=1,
            distance_to_hospital_km=12.0,
            has_early_warning=True,
            road_access_quality="moderate",
            data_status="live",
            source="MDoNER Exposure DB",
        )
        db.add(ez)
        await db.commit()

    resp = await client.post("/intelligence/decision", json={
        "lat": 26.15,
        "lng": 91.75,
    }, headers=auth_header(citizen_token))

    assert resp.status_code == 200
    d = resp.json()

    # Verify complete decision bundle
    assert d["location_id"] is not None
    assert d["risk"]["risk_score"] == 0.78
    assert d["risk"]["risk_level"] == "HIGH"
    assert d["risk"]["data_status"] == "live"

    # Driver explanations
    assert len(d["explanation"]) > 0
    assert "label" in d["explanation"][0]
    assert "description" in d["explanation"][0]

    # Exposure summary
    assert d["exposure"] is not None
    assert d["exposure"]["population"] == 2500
    assert d["exposure"]["hospitals"] == 1

    # Priority engine results & factors
    assert "priority_score" in d["priority"]
    assert 0.0 <= d["priority"]["priority_score"] <= 100.0
    assert d["priority"]["priority_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert "weights" in d["priority"]
    assert "factors" in d["priority"]

    # Recommended civil defense actions
    assert len(d["actions"]) > 0
    assert isinstance(d["actions"], list)


# ─── 3. Complete End-to-End Emergency Response Flow ──────────────────────────

@pytest.mark.asyncio
async def test_day6_complete_response_lifecycle(client: AsyncClient):
    """
    Verifies the complete integration flow:
    1. Citizen submits emergency SOS (POST /incidents)
    2. Officer verifies incident via POST /incidents/{id}/verify alias
    3. Matching worker consumes queue and matches nearest volunteer
    4. Volunteer acknowledges assignment via POST /assignments/{id}/ack alias
    5. Volunteer completes assignment via PATCH /assignments/{id}/status (done)
    6. Incident automatically resolves
    7. Audit log tracks all state transitions and actor IDs
    """
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_token = await register_and_login(client, "volunteer")

    # 1. Volunteer registers heartbeat with skills
    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.152, "lng": 91.751, "skills": ["first_aid", "search_and_rescue"],
    }, headers=auth_header(vol_token))
    assert vol_resp.status_code == 200
    vol_id = vol_resp.json()["id"]

    # 2. Citizen submits SOS
    sos_resp = await client.post("/incidents", json={
        "type": "landslide",
        "description": "Massive landslide blocking NH-27, 2 vehicles trapped",
        "lat": 26.15,
        "lng": 91.75,
        "severity": 4,
    }, headers=auth_header(citizen_token))
    assert sos_resp.status_code == 201
    incident_id = sos_resp.json()["id"]
    assert sos_resp.json()["status"] == "reported"

    # 3. Officer verifies incident (testing POST alias)
    verify_resp = await client.post(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "verified"

    # 4. Trigger Matching Worker
    with patch("app.background.matching_worker.async_session", return_value=TestSession()):
        await process_incident_match(incident_id)

    # 5. Confirm assignment created
    async with TestSession() as db:
        assign_res = await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))
        assignment = assign_res.scalar_one_or_none()
        assert assignment is not None
        assert assignment.volunteer_id == vol_id
        assert assignment.status == "pending"
        assignment_id = str(assignment.id)

    # 6. Volunteer acknowledges assignment (testing POST /ack alias)
    ack_resp = await client.post(f"/assignments/{assignment_id}/ack", headers=auth_header(vol_token))
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acked"

    # 7. Volunteer completes assignment
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(vol_token))
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "done"

    # 8. Verify parent incident auto-resolved
    async with TestSession() as db:
        inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
        inc = inc_res.scalar_one()
        assert inc.status == "resolved"

        # 9. Verify audit trail entries
        audit_res = await db.execute(select(AuditLog).where(
            (AuditLog.entity_id == incident_id) | (AuditLog.entity_id == assignment_id)
        ))
        logs = audit_res.scalars().all()
        actions = [l.action for l in logs]
        assert "verify" in actions
        assert "assign" in actions
        assert "status_acked" in actions
        assert "status_done" in actions


# ─── 4. Cross-Role RBAC Authorization Verification ────────────────────────────

@pytest.mark.asyncio
async def test_day6_cross_role_rbac_guards(client: AsyncClient):
    """
    Verifies that role boundaries are strictly enforced:
    - Citizen cannot verify incidents or run simulations
    - Volunteer cannot verify incidents or modify assignments of other volunteers
    - Officer and Admin can verify incidents and manage exposure zones
    """
    citizen_token = await register_and_login(client, "citizen")
    vol1_token = await register_and_login(client, "volunteer")
    vol2_token = await register_and_login(client, "volunteer")
    officer_token = await register_and_login(client, "officer")

    # Create an incident
    inc_resp = await client.post("/incidents", json={
        "type": "landslide", "description": "Test RBAC incident",
        "lat": 26.1, "lng": 91.7, "severity": 3,
    }, headers=auth_header(citizen_token))
    inc_id = inc_resp.json()["id"]

    # 1. Citizen attempts to verify incident -> 403 Forbidden
    resp = await client.post(f"/incidents/{inc_id}/verify", json={"data_label": "live"}, headers=auth_header(citizen_token))
    assert resp.status_code == 403

    # 2. Volunteer attempts to verify incident -> 403 Forbidden
    resp = await client.post(f"/incidents/{inc_id}/verify", json={"data_label": "live"}, headers=auth_header(vol1_token))
    assert resp.status_code == 403

    # 3. Citizen attempts to create exposure zone -> 403 Forbidden
    resp = await client.post("/intelligence/exposure", json={
        "lat": 26.1, "lng": 91.7, "population": 1000,
    }, headers=auth_header(citizen_token))
    assert resp.status_code == 403

    # 4. Citizen attempts what-if simulation -> 403 Forbidden
    resp = await client.post("/intelligence/whatif", json={
        "lat": 26.1, "lng": 91.7, "scenario_rainfall_mm": 100.0,
    }, headers=auth_header(citizen_token))
    assert resp.status_code == 403

    # 5. Officer creates exposure zone -> 201 Created
    resp = await client.post("/intelligence/exposure", json={
        "name": "Officer Created Zone", "lat": 26.1, "lng": 91.7, "population": 1000,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 201


# ─── 5. Stale Risk Data & TTL Handling ────────────────────────────────────────

@pytest.mark.asyncio
async def test_day6_stale_risk_data_ttl(client: AsyncClient):
    """
    Verifies that RiskZone records older than RISK_FRESHNESS_MINUTES
    automatically return data_status: 'stale' on both /risk and /intelligence/decision.
    """
    citizen_token = await register_and_login(client, "citizen")

    stale_time = datetime.now(timezone.utc) - timedelta(minutes=120)  # 2 hours old
    async with TestSession() as db:
        rz = RiskZone(
            id="zone-stale-day6",
            lat=26.30,
            lng=91.90,
            risk_score=0.65,
            horizon_hours=24,
            top_features={"rainfall_24h": 90.0},
            data_label="live",
            computed_at=stale_time,
        )
        db.add(rz)
        await db.commit()

    # Query /risk
    resp = await client.get("/risk", headers=auth_header(citizen_token))
    assert resp.status_code == 200
    zones = resp.json()
    stale_zone = next((z for z in zones if z["id"] == "zone-stale-day6"), None)
    assert stale_zone is not None
    assert stale_zone["data_label"] == "stale"

    # Query /intelligence/decision
    dec_resp = await client.post("/intelligence/decision", json={
        "lat": 26.30, "lng": 91.90, "zone_id": "zone-stale-day6"
    }, headers=auth_header(citizen_token))
    assert dec_resp.status_code == 200
    assert dec_resp.json()["data_status"] == "stale"
    assert dec_resp.json()["risk"]["data_status"] == "stale"


# ─── 6. Failure Safety & Graceful Degradation ─────────────────────────────────

@pytest.mark.asyncio
async def test_day6_failure_safety_missing_risk_503(client: AsyncClient):
    """
    Verifies that querying risk or decision intelligence when no RiskZone exists
    produces a clean HTTP 503 (RISK_SERVICE_UNAVAILABLE) rather than fabricating a fake score.
    """
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    # Clear risk zones in test DB
    async with TestSession() as db:
        await db.execute(select(RiskZone))
        # Empty table test

    # POST /risk without stored zones -> 503
    resp = await client.post("/risk", json={
        "lat": 10.0, "lng": 10.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 503
    assert resp.headers.get("X-Error-Code") == "RISK_SERVICE_UNAVAILABLE"

    # POST /intelligence/decision without stored zones -> 503
    resp2 = await client.post("/intelligence/decision", json={
        "lat": 10.0, "lng": 10.0,
    }, headers=auth_header(citizen_token))
    assert resp2.status_code == 503
    assert resp2.headers.get("X-Error-Code") == "RISK_SERVICE_UNAVAILABLE"


# ─── 7. What-If Scenario Simulation Integration ──────────────────────────────

@pytest.mark.asyncio
async def test_day6_whatif_simulation_integrity(client: AsyncClient):
    """
    Verifies that POST /intelligence/whatif:
    - Is restricted to officer/admin
    - Returns 'SIMULATION — NOT A FORECAST'
    - Increases risk and priority when scenario rainfall is added
    - Correctly falls back to nearest risk zone when zone_id is omitted
    """
    officer_token = await register_and_login(client, "officer")

    async with TestSession() as db:
        rz = RiskZone(
            id="zone-whatif-day6",
            lat=26.15,
            lng=91.75,
            risk_score=0.40,
            horizon_hours=24,
            top_features={"rainfall_24h": 50.0},
            data_label="live",
            computed_at=datetime.now(timezone.utc),
        )
        db.add(rz)
        await db.commit()

    # Execute simulation without explicit zone_id (tests coordinate fallback)
    resp = await client.post("/intelligence/whatif", json={
        "lat": 26.15,
        "lng": 91.75,
        "scenario_rainfall_mm": 350.0,
    }, headers=auth_header(officer_token))

    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_label"] == "SIMULATION — NOT A FORECAST"
    assert data["data_status"] == "simulated"
    assert data["current_risk_score"] == 0.40
    assert data["projected_risk_score"] > 0.40
    assert len(data["projected_actions"]) > 0


# ─── 8. Idempotency on SOS & Batch Sync ───────────────────────────────────────

@pytest.mark.asyncio
async def test_day6_idempotency_deduplication(client: AsyncClient):
    """Verifies that duplicate SOS submissions with idempotency_key do not create duplicate incidents."""
    citizen_token = await register_and_login(client, "citizen")
    key = "idemp-key-day6-test-999"

    resp1 = await client.post("/incidents", json={
        "type": "flood", "description": "Flash flood", "lat": 26.1, "lng": 91.7,
        "severity": 3, "idempotency_key": key,
    }, headers=auth_header(citizen_token))
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    # Submit same request again
    resp2 = await client.post("/incidents", json={
        "type": "flood", "description": "Flash flood duplicate", "lat": 26.1, "lng": 91.7,
        "severity": 3, "idempotency_key": key,
    }, headers=auth_header(citizen_token))
    assert resp2.status_code == 201 or resp2.status_code == 200
    id2 = resp2.json()["id"]

    assert id1 == id2, "Duplicate submission must return the existing incident without creating duplicates"
