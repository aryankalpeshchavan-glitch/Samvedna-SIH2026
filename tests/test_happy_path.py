import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy import select

from unittest.mock import patch

from app.core.database import async_session
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from tests.test_api import auth_header, register_and_login, TestSession, client, setup_db
from app.background.matching_worker import process_incident_match


@pytest.mark.asyncio
async def test_full_happy_path(client: AsyncClient):
    """
    Tests the complete happy path:
    Citizen SOS → Officer verifies → matching selects volunteer → assignment created → volunteer ACK → volunteer done → incident resolved
    """
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_token = await register_and_login(client, "volunteer")

    # 0. Volunteer registers location & skills
    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.75, "skills": ["rescue", "swimming"],
    }, headers=auth_header(vol_token))
    assert vol_resp.status_code == 200
    vol_id = vol_resp.json()["id"]

    # 1. Citizen SOS (Create Incident)
    inc_resp = await client.post("/incidents", json={
        "type": "flood", "description": "Citizen SOS: trapped in flood",
        "lat": 26.15, "lng": 91.75, "severity": 4,
    }, headers=auth_header(citizen_token))
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    # 2. Officer verifies
    verify_resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "verified"

    # 3. Matching selects volunteer -> Assignment created
    with patch("app.background.matching_worker.async_session", return_value=TestSession()):
        await process_incident_match(incident_id)

    # 4. Check that assignment was created
    async with TestSession() as db:
        result = await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))
        assignment = result.scalar_one_or_none()
        assert assignment is not None, "Assignment should be created by matching worker"
        assert assignment.volunteer_id == vol_id
        assert assignment.status == "pending"
        assignment_id = str(assignment.id)

    # 5. Volunteer ACK
    ack_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "acked"
    }, headers=auth_header(vol_token))
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acked"

    # 6. Volunteer Done -> Incident Resolved
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(vol_token))
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "done"

    # 7. Check final incident status
    async with TestSession() as db:
        inc_res = await db.execute(select(Incident).where(Incident.id == incident_id))
        final_incident = inc_res.scalar_one()
        assert final_incident.status == "resolved"

        # 8. Check audit trail
        audit_res = await db.execute(select(AuditLog).where(
            (AuditLog.entity_id == incident_id) | (AuditLog.entity_id == assignment_id)
        ))
        logs = audit_res.scalars().all()
        actions = [log.action for log in logs]
        
        # Incident creation (via DB listeners) and verify (via API)
        assert "verify" in actions

        # Assignment creation (worker)
        assert "assign" in actions

        # Assignment status changes (API)
        assert "status_acked" in actions
        assert "status_done" in actions
