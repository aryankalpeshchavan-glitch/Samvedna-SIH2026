import pytest
from httpx import AsyncClient
from sqlalchemy import select
from unittest.mock import patch, AsyncMock

from app.core.database import async_session
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from app.models.volunteer import Volunteer
from tests.test_api import auth_header, register_and_login, TestSession, client, setup_db
from app.background.matching_worker import process_incident_match


@pytest.mark.asyncio
async def test_admin_reject_incident(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    # 1. Citizen creates incident
    resp = await client.post("/incidents", json={
        "type": "flood", "description": "False alarm report",
        "lat": 26.15, "lng": 91.75, "severity": 1,
    }, headers=auth_header(citizen_token))
    assert resp.status_code == 201
    incident_id = resp.json()["id"]

    # 2. Citizen cannot reject
    rej_resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(citizen_token))
    assert rej_resp.status_code == 403

    # 3. Officer rejects
    rej_resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))
    assert rej_resp.status_code == 200
    assert rej_resp.json()["status"] == "rejected"

    # 4. Cannot verify a rejected incident
    ver_resp = await client.patch(f"/incidents/{incident_id}/verify", json={"data_label": "live"}, headers=auth_header(officer_token))
    assert ver_resp.status_code == 400

    # 5. Check audit log has "reject"
    async with TestSession() as db:
        logs = await db.execute(select(AuditLog).where(AuditLog.entity_id == incident_id, AuditLog.action == "reject"))
        assert len(logs.scalars().all()) == 1


@pytest.mark.asyncio
async def test_assignment_rbac_and_invalid_transitions(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")
    vol1_token = await register_and_login(client, "volunteer")
    vol2_token = await register_and_login(client, "volunteer")

    # Setup volunteer 1
    vol1_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.75, "skills": ["rescue"],
    }, headers=auth_header(vol1_token))
    vol1_id = vol1_resp.json()["id"]

    # Setup volunteer 2
    vol2_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.16, "lng": 91.76, "skills": ["first_aid"],
    }, headers=auth_header(vol2_token))
    vol2_id = vol2_resp.json()["id"]

    # Create incident
    inc_resp = await client.post("/incidents", json={
        "type": "landslide", "description": "Rockfall on highway",
        "lat": 26.15, "lng": 91.75, "severity": 3,
    }, headers=auth_header(officer_token))
    incident_id = inc_resp.json()["id"]

    # Assign to vol1
    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol1_id, "sla_minutes": 5,
    }, headers=auth_header(officer_token))
    assert assign_resp.status_code == 201
    assignment_id = assign_resp.json()["id"]

    # Duplicate active assignment should be rejected
    dup_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol2_id, "sla_minutes": 5,
    }, headers=auth_header(officer_token))
    assert dup_resp.status_code == 400

    # Vol2 cannot modify Vol1's assignment
    bad_ack = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "acked"
    }, headers=auth_header(vol2_token))
    assert bad_ack.status_code == 403

    # Vol1 cannot transition directly from pending to done
    invalid_trans = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(vol1_token))
    assert invalid_trans.status_code == 400

    # Vol1 ACKs successfully
    ack_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "acked"
    }, headers=auth_header(vol1_token))
    assert ack_resp.status_code == 200

    # Duplicate ACK is idempotent (succeeds)
    dup_ack = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "acked"
    }, headers=auth_header(vol1_token))
    assert dup_ack.status_code == 200

    # Vol1 marks in_progress
    prog_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "in_progress"
    }, headers=auth_header(vol1_token))
    assert prog_resp.status_code == 200

    # Vol1 marks done
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(vol1_token))
    assert done_resp.status_code == 200

    # Vol1 checks own assignments
    my_resp = await client.get("/assignments/my", headers=auth_header(vol1_token))
    assert my_resp.status_code == 200
    assert len(my_resp.json()) >= 1


@pytest.mark.asyncio
async def test_matching_worker_no_resource_available(client: AsyncClient):
    """When no volunteers are available, matching worker logs matching_no_resource and does not crash."""
    officer_token = await register_and_login(client, "officer")

    inc_resp = await client.post("/incidents", json={
        "type": "flood", "description": "Isolated flood area",
        "lat": 28.0, "lng": 94.0, "severity": 4,
    }, headers=auth_header(officer_token))
    incident_id = inc_resp.json()["id"]

    await client.patch(f"/incidents/{incident_id}/verify", json={"data_label": "live"}, headers=auth_header(officer_token))

    # Process match with no available volunteers in DB
    with patch("app.background.matching_worker.async_session", return_value=TestSession()):
        await process_incident_match(incident_id)

    async with TestSession() as db:
        # Assignment should not be created
        assigns = await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))
        assert len(assigns.scalars().all()) == 0

        # Audit log should record matching_no_resource
        logs = await db.execute(select(AuditLog).where(
            AuditLog.entity_id == incident_id,
            AuditLog.action == "matching_no_resource"
        ))
        assert len(logs.scalars().all()) == 1


@pytest.mark.asyncio
async def test_risk_api_contract(client: AsyncClient):
    """Test POST /risk contract returns expected keys."""
    citizen_token = await register_and_login(client, "citizen")

    resp = await client.post("/risk", json={
        "lat": 26.15,
        "lng": 91.75,
        "horizon_hours": 24,
        "features": {"rainfall_24h": 120.5, "rainfall_7day": 340.2}
    }, headers=auth_header(citizen_token))

    assert resp.status_code == 200
    data = resp.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "confidence" in data
    assert "drivers" in data
    assert "data_status" in data
    assert isinstance(data["drivers"], list)
