"""
Step 4C: Critical-Path Integration Test Suite
============================================
Validates end-to-end integration and reliability invariants across:
1. Complete lifecycle and audit trail:
   reported -> verified -> worker match (fresh vs stale/busy pool) -> pending ->
   ACK (acked) -> in_progress -> done -> resolved, validating database consistency,
   status endpoints, and chronological AuditLog trail.
2. No-resource and recovery:
   verified incident with 0 eligible volunteers -> matching_no_resource audit event ->
   incident remains verified -> volunteer registers fresh heartbeat -> re-match creates pending assignment.
3. Multi-hop reassignment to exhaustion:
   Vol 1 assignment expires -> auto-reassigns to Vol 2 (Vol 1 excluded) ->
   Vol 2 expires -> exhaustion reverts incident to verified with 0 active assignments
   and reassign_exhausted audit event.
4. Concurrent matching worker race:
   asyncio.gather on two simultaneous process_incident_match executions for the same
   incident guarantees clean collision handling without unhandled exceptions and exactly
   one active assignment.
"""
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.core.config import settings
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.audit import AuditLog
from app.models.volunteer import Volunteer
from app.background.matching_worker import process_incident_match
from app.background.auto_reassign import check_and_reassign_expired
from tests.test_api import auth_header, register_and_login, TestSession, client, setup_db


@pytest.fixture(autouse=True)
def override_worker_db():
    with patch("app.background.matching_worker.async_session", TestSession), \
         patch("app.background.auto_reassign.async_session", TestSession):
        yield


# ─── 1. Full Lifecycle & Continuous Audit Trail ──────────────────────────────

@pytest.mark.asyncio
async def test_critical_path_full_lifecycle_and_audit_trail(client: AsyncClient):
    """
    Validates the complete end-to-end response lifecycle:
    1. Candidate pool includes stale, busy, and fresh volunteers.
    2. Citizen SOS creates reported incident.
    3. Officer verifies incident (reported -> verified).
    4. Matching worker assigns ONLY the live eligible volunteer (verified -> assigned, status=pending).
    5. Volunteer acknowledges (pending -> acked).
    6. Volunteer starts response (acked -> in_progress).
    7. Volunteer finishes response (in_progress -> done, incident -> resolved).
    8. Verifies status consistency across Incident, Assignment, GET /status/{id}, and AuditLog.
    """
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_stale_token = await register_and_login(client, "volunteer")
    vol_busy_token = await register_and_login(client, "volunteer")
    vol_fresh_token = await register_and_login(client, "volunteer")

    # 1. Setup candidate volunteer pool:
    # Stale volunteer (available, but heartbeat > 30 min old)
    r_stale = await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.75, "skills": ["rescue", "swimming"],
        "availability_status": "available",
    }, headers=auth_header(vol_stale_token))
    assert r_stale.status_code == 200
    stale_vol_id = r_stale.json()["id"]

    # Explicitly mark heartbeat stale in the database
    async with TestSession() as db:
        await db.execute(
            update(Volunteer).where(Volunteer.id == stale_vol_id).values(
                last_heartbeat=datetime.utcnow() - timedelta(minutes=settings.VOLUNTEER_HEARTBEAT_TIMEOUT_MINUTES + 15)
            )
        )
        await db.commit()

    # Busy volunteer (fresh heartbeat, but availability_status="busy")
    r_busy = await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.75, "skills": ["rescue", "swimming"],
        "availability_status": "busy",
    }, headers=auth_header(vol_busy_token))
    assert r_busy.status_code == 200
    busy_vol_id = r_busy.json()["id"]

    # Fresh eligible volunteer (fresh heartbeat, availability_status="available")
    r_fresh = await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.75, "skills": ["rescue", "swimming"],
        "availability_status": "available",
    }, headers=auth_header(vol_fresh_token))
    assert r_fresh.status_code == 200
    fresh_vol_id = r_fresh.json()["id"]

    # 2. Citizen creates incident (SOS)
    sos_resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Flash flood in riverbank colony, families stranded",
        "lat": 26.15,
        "lng": 91.75,
        "severity": 4,
    }, headers=auth_header(citizen_token))
    assert sos_resp.status_code == 201
    incident_id = sos_resp.json()["id"]
    assert sos_resp.json()["status"] == "reported"

    # Verify status endpoint & DB state for reported incident
    st_rep = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_rep.status_code == 200
    assert st_rep.json()["status"] == "reported"

    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "reported"
        assign_count = len((await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))).scalars().all())
        assert assign_count == 0

    # 3. Officer verifies incident
    verify_resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live",
    }, headers=auth_header(officer_token))
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "verified"

    # Verify status endpoint & DB state for verified incident
    st_ver = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_ver.status_code == 200
    assert st_ver.json()["status"] == "verified"

    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "verified"

    # 4. Matching worker processes incident match
    with patch("app.notifications.dispatcher.on_assignment_created", new_callable=AsyncMock):
        await process_incident_match(incident_id)

    # Verify assignment creation and status consistency
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"

        res = await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))
        assignments = res.scalars().all()
        assert len(assignments) == 1
        active_assignment = assignments[0]

        # STALE and BUSY volunteers must be strictly excluded; fresh_vol_id must be assigned
        assert active_assignment.volunteer_id == fresh_vol_id
        assert active_assignment.volunteer_id != stale_vol_id
        assert active_assignment.volunteer_id != busy_vol_id
        assert active_assignment.status == "pending"
        assignment_id = str(active_assignment.id)

    # Check status endpoint reflects assigned
    st_asg = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_asg.status_code == 200
    assert st_asg.json()["status"] == "assigned"

    # 5. Volunteer acknowledges assignment
    ack_resp = await client.post(f"/assignments/{assignment_id}/ack", headers=auth_header(vol_fresh_token))
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "acked"

    async with TestSession() as db:
        a = (await db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one()
        assert a.status == "acked"
        assert a.acked_at is not None
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"

    st_ack = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_ack.status_code == 200
    assert st_ack.json()["status"] == "assigned"

    # 6. Volunteer transitions assignment to in_progress
    prog_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "in_progress",
    }, headers=auth_header(vol_fresh_token))
    assert prog_resp.status_code == 200
    assert prog_resp.json()["status"] == "in_progress"

    async with TestSession() as db:
        a = (await db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one()
        assert a.status == "in_progress"
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"

    st_prog = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_prog.status_code == 200
    assert st_prog.json()["status"] == "assigned"

    # 7. Volunteer completes assignment (status=done) -> Incident auto-resolves
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done",
    }, headers=auth_header(vol_fresh_token))
    assert done_resp.status_code == 200
    assert done_resp.json()["status"] == "done"

    async with TestSession() as db:
        a = (await db.execute(select(Assignment).where(Assignment.id == assignment_id))).scalar_one()
        assert a.status == "done"
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "resolved"

    st_done = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_done.status_code == 200
    assert st_done.json()["status"] == "resolved"

    # 8. Chronological AuditLog events verification
    async with TestSession() as db:
        audit_res = await db.execute(
            select(AuditLog)
            .where((AuditLog.entity_id == incident_id) | (AuditLog.entity_id == assignment_id))
            .order_by(AuditLog.timestamp.asc(), AuditLog.id.asc())
        )
        logs = audit_res.scalars().all()
        actions = [log.action for log in logs]

        # Verify all key lifecycle events are recorded in the audit trail
        assert "verify" in actions
        assert "assign" in actions
        assert "status_acked" in actions
        assert "status_in_progress" in actions
        assert "status_done" in actions

        # Verify state deltas for each action
        verify_log = next(l for l in logs if l.action == "verify")
        assert verify_log.entity_type == "Incident"
        assert verify_log.before["status"] == "reported"
        assert verify_log.after["status"] == "verified"

        assign_log = next(l for l in logs if l.action == "assign")
        assert assign_log.entity_type == "Assignment"
        assert assign_log.after["status"] == "pending"
        assert assign_log.after["volunteer_id"] == fresh_vol_id

        ack_log = next(l for l in logs if l.action == "status_acked")
        assert ack_log.before["status"] == "pending"
        assert ack_log.after["status"] == "acked"

        prog_log = next(l for l in logs if l.action == "status_in_progress")
        assert prog_log.before["status"] == "acked"
        assert prog_log.after["status"] == "in_progress"

        done_log = next(l for l in logs if l.action == "status_done")
        assert done_log.before["status"] == "in_progress"
        assert done_log.after["status"] == "done"


# ─── 2. No-Resource and Recovery Flow ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_critical_path_no_resource_and_recovery(client: AsyncClient):
    """
    Validates no-resource handling and subsequent volunteer recovery:
    1. Incident is verified with zero eligible volunteers available.
    2. Matching worker runs, logs matching_no_resource audit event.
    3. Incident status remains verified; zero assignments created.
    4. A volunteer becomes active and submits fresh heartbeat.
    5. Matching worker runs again, successfully matches and creates pending assignment.
    """
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    # 1. Create and verify incident
    resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Submerged road, isolated area",
        "lat": 26.18,
        "lng": 91.78,
        "severity": 3,
    }, headers=auth_header(citizen_token))
    incident_id = resp.json()["id"]

    await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live",
    }, headers=auth_header(officer_token))

    # 2. Run matching worker with no eligible volunteers in DB
    with patch("app.notifications.dispatcher.on_assignment_created", new_callable=AsyncMock):
        await process_incident_match(incident_id)

    # 3. Assert incident remains verified, no assignment created, and audit logged
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "verified"

        assigns = (await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))).scalars().all()
        assert len(assigns) == 0

        audit_res = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_id == incident_id,
                AuditLog.action == "matching_no_resource",
            )
        )
        no_res_logs = audit_res.scalars().all()
        assert len(no_res_logs) == 1
        assert no_res_logs[0].after["reason"] == "no_available_volunteers"

    # Status endpoint confirms incident is still verified
    st_resp = await client.get(f"/status/{incident_id}", headers=auth_header(citizen_token))
    assert st_resp.json()["status"] == "verified"

    # 4. Volunteer arrives: registers fresh heartbeat with available status
    vol_token = await register_and_login(client, "volunteer")
    v_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.18, "lng": 91.78, "skills": ["rescue"],
        "availability_status": "available",
    }, headers=auth_header(vol_token))
    assert v_resp.status_code == 200
    new_vol_id = v_resp.json()["id"]

    # 5. Re-run matching worker
    with patch("app.notifications.dispatcher.on_assignment_created", new_callable=AsyncMock):
        await process_incident_match(incident_id)

    # 6. Assert assignment is now created and incident is assigned
    async with TestSession() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"

        assigns = (await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))).scalars().all()
        assert len(assigns) == 1
        assert assigns[0].volunteer_id == new_vol_id
        assert assigns[0].status == "pending"

        assign_audit = (await db.execute(
            select(AuditLog).where(
                AuditLog.entity_id == str(assigns[0].id),
                AuditLog.action == "assign",
            )
        )).scalars().all()
        assert len(assign_audit) == 1


# ─── 3. Multi-Hop Reassignment to Exhaustion ─────────────────────────────────

@pytest.mark.asyncio
async def test_critical_path_end_to_end_reassignment_to_exhaustion(client: AsyncClient):
    """
    Validates multi-hop assignment expiry and graceful exhaustion:
    1. Vol 1 receives assignment; expires without ACK.
    2. Auto-reassign reallocates to Vol 2, strictly excluding Vol 1.
    3. Vol 2 expires without ACK.
    4. No replacement volunteers remain:
       - Old assignments marked 'reassigned'.
       - Zero active assignments remain.
       - Incident returns to 'verified' state.
       - Exactly one 'reassign_exhausted' audit event is logged.
    """
    officer_token = await register_and_login(client, "officer")
    vol1_token = await register_and_login(client, "volunteer")
    vol2_token = await register_and_login(client, "volunteer")

    v1_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.14, "lng": 91.73, "skills": ["rescue"], "availability_status": "available",
    }, headers=auth_header(vol1_token))
    v1_id = v1_resp.json()["id"]

    v2_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.74, "skills": ["rescue"], "availability_status": "available",
    }, headers=auth_header(vol2_token))
    v2_id = v2_resp.json()["id"]

    # Create & verify incident
    inc_resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Multi-hop reassignment exhaustion test",
        "lat": 26.14,
        "lng": 91.73,
        "severity": 3,
    }, headers=auth_header(officer_token))
    incident_id = inc_resp.json()["id"]

    await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live",
    }, headers=auth_header(officer_token))

    # Initial match: Vol 1 is matched
    with patch("app.notifications.dispatcher.on_assignment_created", new_callable=AsyncMock):
        await process_incident_match(incident_id)

    async with TestSession() as db:
        a1 = (await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))).scalar_one()
        assert a1.status == "pending"
        a1_id = str(a1.id)
        assigned_vol1_id = a1.volunteer_id

        # Simulate Vol 1 SLA expiration
        a1.sla_deadline = datetime.utcnow() - timedelta(seconds=10)
        await db.commit()

    # Run auto-reassign loop
    with patch("app.notifications.dispatcher.on_assignment_reassigned", new_callable=AsyncMock):
        await check_and_reassign_expired()

    # Verify first reassignment: a1 -> reassigned, a2 -> pending (assigned to second volunteer)
    async with TestSession() as db:
        all_assigns = (await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))).scalars().all()
        assert len(all_assigns) == 2

        old_a = next(a for a in all_assigns if a.id == a1_id)
        new_a = next(a for a in all_assigns if a.id != a1_id)

        assert old_a.status == "reassigned"
        assert new_a.status == "pending"
        # Immediate predecessor must be excluded
        assert new_a.volunteer_id != assigned_vol1_id
        a2_id = str(new_a.id)

        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"

        # Simulate Vol 2 SLA expiration
        new_a.sla_deadline = datetime.utcnow() - timedelta(seconds=10)
        await db.commit()

    # Run auto-reassign loop again (no replacement available; both Vol 1 & Vol 2 are historical)
    with patch("app.notifications.dispatcher.on_assignment_reassigned", new_callable=AsyncMock):
        await check_and_reassign_expired()

    # Verify exhaustion behavior:
    async with TestSession() as db:
        all_assigns = (await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))).scalars().all()
        assert len(all_assigns) == 2
        # All historical assignments must be 'reassigned'
        for a in all_assigns:
            assert a.status == "reassigned"

        # Invariant: exactly 0 active assignments
        active_assigns = [a for a in all_assigns if a.status in ["pending", "acked", "in_progress"]]
        assert len(active_assigns) == 0

        # Incident status returns to verified (not stranded in assigned)
        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "verified"

        # Verify reassign_exhausted audit log entry
        audit_res = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_id == incident_id,
                AuditLog.action == "reassign_exhausted",
            )
        )
        exhaust_logs = audit_res.scalars().all()
        assert len(exhaust_logs) == 1
        log = exhaust_logs[0]
        assert log.before["status"] == "assigned"
        assert log.after["status"] == "verified"
        assert log.after["reason"] == "no_available_replacement_volunteers"


# ─── 4. Concurrent Matching Worker Race ──────────────────────────────────────

@pytest.mark.asyncio
async def test_critical_path_concurrent_matching_worker_race(client: AsyncClient):
    """
    Simulates two matching workers executing concurrently for the exact same verified incident.
    Verifies that:
    1. The operation completes cleanly without unhandled exceptions or crashes.
    2. Exactly ONE active assignment is created in the database.
    3. The partial unique index uix_active_assignment_per_incident guarantees zero duplicate active assignments.
    4. Incident status remains consistently 'assigned'.
    """
    officer_token = await register_and_login(client, "officer")
    vol1_token = await register_and_login(client, "volunteer")
    vol2_token = await register_and_login(client, "volunteer")

    await client.post("/volunteers/heartbeat", json={
        "lat": 26.15, "lng": 91.75, "skills": ["rescue"], "availability_status": "available",
    }, headers=auth_header(vol1_token))

    await client.post("/volunteers/heartbeat", json={
        "lat": 26.16, "lng": 91.76, "skills": ["rescue"], "availability_status": "available",
    }, headers=auth_header(vol2_token))

    inc_resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Concurrent matching race test",
        "lat": 26.15,
        "lng": 91.75,
        "severity": 3,
    }, headers=auth_header(officer_token))
    incident_id = inc_resp.json()["id"]

    await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live",
    }, headers=auth_header(officer_token))

    # Execute two matching worker tasks simultaneously on the same incident
    with patch("app.notifications.dispatcher.on_assignment_created", new_callable=AsyncMock):
        results = await asyncio.gather(
            process_incident_match(incident_id),
            process_incident_match(incident_id),
            return_exceptions=True,
        )

    # 1. Assert no unhandled exceptions were raised
    for res in results:
        assert not isinstance(res, Exception), f"Unexpected exception in worker: {res}"

    # 2. Assert exactly one active assignment exists in the database
    async with TestSession() as db:
        res = await db.execute(select(Assignment).where(Assignment.incident_id == incident_id))
        all_assigns = res.scalars().all()
        active_assigns = [a for a in all_assigns if a.status in ["pending", "acked", "in_progress"]]

        assert len(active_assigns) == 1
        assert len(all_assigns) == 1
        assert active_assigns[0].status == "pending"

        inc = (await db.execute(select(Incident).where(Incident.id == incident_id))).scalar_one()
        assert inc.status == "assigned"
