"""
Step 2A: Incident State Transition Hardening Test Suite
======================================================
Tests all 12 required state transition and idempotency invariants:
1. reported -> verified succeeds.
2. verified -> verify:
   - returns HTTP 200
   - remains verified
   - no duplicate audit log
   - no duplicate Redis matching job
3. assigned -> verify:
   - returns HTTP 400
   - remains assigned
   - active assignment remains untouched
4. reported -> rejected succeeds.
5. verified -> rejected succeeds.
6. assigned -> rejected:
   - returns HTTP 400
   - remains assigned
   - active assignment remains untouched
7. resolved -> verify:
   - returns HTTP 400
8. resolved -> reject:
   - returns HTTP 400
9. rejected -> verify:
   - returns HTTP 400
10. rejected -> reject:
   - returns HTTP 400
11. Verify RBAC: citizen/volunteer cannot verify (HTTP 403).
12. Reject RBAC: citizen/volunteer cannot reject (HTTP 403).
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from unittest.mock import patch, AsyncMock

from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from tests.test_api import auth_header, client, register_and_login, setup_db, TestSession


async def _create_test_incident(client: AsyncClient, token: str) -> str:
    res = await client.post("/incidents", json={
        "type": "landslide",
        "description": "Debris on road",
        "lat": 26.15,
        "lng": 91.75,
        "severity": 3,
    }, headers=auth_header(token))
    assert res.status_code == 201
    return res.json()["id"]


async def _create_test_assignment(client: AsyncClient, officer_token: str, incident_id: str) -> tuple[str, int]:
    vol_token = await register_and_login(client, "volunteer")
    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.16, "lng": 91.76, "skills": ["rescue"],
    }, headers=auth_header(vol_token))
    assert vol_resp.status_code == 200
    vol_id = vol_resp.json()["id"]

    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id,
        "volunteer_id": vol_id,
    }, headers=auth_header(officer_token))
    assert assign_resp.status_code == 201
    return assign_resp.json()["id"], vol_id


# ─── 1. reported -> verified succeeds ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_reported_to_verified_succeeds(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)

    resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "verified"
    assert data["data_label"] == "live"


# ─── 2. verified -> verify is idempotent (no duplicate audit/matching) ────────

@pytest.mark.asyncio
async def test_verified_to_verify_idempotent(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)

    # Initial verification
    resp1 = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert resp1.status_code == 200

    # Count audit logs after initial verification
    async with TestSession() as db:
        res = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_id == incident_id,
                AuditLog.action == "verify",
            )
        )
        initial_audit_count = len(res.scalars().all())
        assert initial_audit_count == 1

    # Second verification attempt with mock matching queue
    with patch("app.routers.incidents.enqueue_matching_job", new_callable=AsyncMock) as mock_enqueue:
        resp2 = await client.patch(f"/incidents/{incident_id}/verify", json={
            "data_label": "live"
        }, headers=auth_header(officer_token))
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "verified"
        # Must NOT re-enqueue matching job
        mock_enqueue.assert_not_called()

    # Verify no duplicate audit log was written
    async with TestSession() as db:
        res = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_id == incident_id,
                AuditLog.action == "verify",
            )
        )
        assert len(res.scalars().all()) == 1


# ─── 3. assigned -> verify fails with HTTP 400 ────────────────────────────────

@pytest.mark.asyncio
async def test_assigned_to_verify_rejected(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    assignment_id, vol_id = await _create_test_assignment(client, officer_token, incident_id)

    # Incident is now in 'assigned' state; attempting to verify must fail
    resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "Cannot verify incident in 'assigned' state" in resp.text

    # Verify incident remains 'assigned' and assignment is untouched
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"
        assign = (await db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one()
        assert assign.status == "pending"


# ─── 4. reported -> rejected succeeds ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_reported_to_rejected_succeeds(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)

    resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


# ─── 5. verified -> rejected succeeds ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_verified_to_rejected_succeeds(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    await client.patch(f"/incidents/{incident_id}/verify", json={"data_label": "live"}, headers=auth_header(officer_token))

    resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


# ─── 6. assigned -> rejected fails with HTTP 400 ──────────────────────────────

@pytest.mark.asyncio
async def test_assigned_to_rejected_rejected(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    assignment_id, vol_id = await _create_test_assignment(client, officer_token, incident_id)

    # Attempting to reject an assigned incident must fail
    resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "Cannot reject incident in 'assigned' state" in resp.text

    # Verify incident remains assigned and assignment is untouched
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"
        assign = (await db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one()
        assert assign.status == "pending"


# ─── 7. resolved -> verify fails with HTTP 400 ────────────────────────────────

@pytest.mark.asyncio
async def test_resolved_to_verify_rejected(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    assignment_id, vol_id = await _create_test_assignment(client, officer_token, incident_id)

    # Transition assignment: pending -> acked -> done
    ack_resp = await client.post(f"/assignments/{assignment_id}/ack", headers=auth_header(officer_token))
    assert ack_resp.status_code == 200
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(officer_token))
    assert done_resp.status_code == 200

    # Verify incident is indeed resolved
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "resolved"

    # Attempt verify on resolved incident
    resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "Cannot verify incident in 'resolved' state" in resp.text


# ─── 8. resolved -> reject fails with HTTP 400 ────────────────────────────────

@pytest.mark.asyncio
async def test_resolved_to_reject_rejected(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    assignment_id, vol_id = await _create_test_assignment(client, officer_token, incident_id)

    # Transition assignment: pending -> acked -> done
    ack_resp = await client.post(f"/assignments/{assignment_id}/ack", headers=auth_header(officer_token))
    assert ack_resp.status_code == 200
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(officer_token))
    assert done_resp.status_code == 200

    # Verify incident is indeed resolved
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "resolved"

    # Attempt reject on resolved incident
    resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "Cannot reject incident in 'resolved' state" in resp.text


# ─── 9. rejected -> verify fails with HTTP 400 ────────────────────────────────

@pytest.mark.asyncio
async def test_rejected_to_verify_rejected(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))

    # Attempt verify on rejected incident
    resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "Cannot verify incident in 'rejected' state" in resp.text


# ─── 10. rejected -> reject fails with HTTP 400 ───────────────────────────────

@pytest.mark.asyncio
async def test_rejected_to_reject_rejected(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    incident_id = await _create_test_incident(client, citizen_token)
    await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))

    # Attempt reject again on rejected incident
    resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "Cannot reject incident in 'rejected' state" in resp.text


# ─── 11. Verify RBAC: citizen/volunteer cannot verify ─────────────────────────

@pytest.mark.asyncio
async def test_verify_rbac_forbidden_for_citizen_and_volunteer(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    vol_token = await register_and_login(client, "volunteer")

    incident_id = await _create_test_incident(client, citizen_token)

    # Citizen cannot verify
    c_resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(citizen_token))
    assert c_resp.status_code == 403

    # Volunteer cannot verify
    v_resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(vol_token))
    assert v_resp.status_code == 403


# ─── 12. Reject RBAC: citizen/volunteer cannot reject ─────────────────────────

@pytest.mark.asyncio
async def test_reject_rbac_forbidden_for_citizen_and_volunteer(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    vol_token = await register_and_login(client, "volunteer")

    incident_id = await _create_test_incident(client, citizen_token)

    # Citizen cannot reject
    c_resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(citizen_token))
    assert c_resp.status_code == 403

    # Volunteer cannot reject
    v_resp = await client.patch(f"/incidents/{incident_id}/reject", headers=auth_header(vol_token))
    assert v_resp.status_code == 403
