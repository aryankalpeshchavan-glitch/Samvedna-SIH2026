import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy import select

from app.core.database import async_session
from app.models.audit import AuditLog
from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.volunteer import Volunteer
from app.models.user import User
from app.background.auto_reassign import check_and_reassign_expired
from tests.test_api import auth_header, register_and_login, client, setup_db, TestSession


@pytest.mark.asyncio
async def test_audit_log_on_incident_verify(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    # 1. Create incident
    inc_resp = await client.post("/incidents", json={
        "type": "flood", "description": "Bridge flooded",
        "lat": 26.15, "lng": 91.75, "severity": 3,
    }, headers=auth_header(citizen_token))
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    # 2. Verify incident
    verify_resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live"
    }, headers=auth_header(officer_token))
    assert verify_resp.status_code == 200

    # 3. Check audit log in DB
    async with TestSession() as db:
        result = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "Incident",
                AuditLog.entity_id == incident_id,
                AuditLog.action == "verify"
            )
        )
        logs = result.scalars().all()
        assert len(logs) >= 1
        audit = logs[0]
        assert audit.action == "verify"
        assert audit.before["status"] == "reported"
        assert audit.after["status"] == "verified"
        assert audit.after["data_label"] == "live"


@pytest.mark.asyncio
async def test_audit_log_on_assignment_lifecycle(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_token = await register_and_login(client, "volunteer")

    inc_resp = await client.post("/incidents", json={
        "type": "landslide", "description": "Hill road blocked",
        "lat": 26.2, "lng": 91.8, "severity": 4,
    }, headers=auth_header(citizen_token))
    incident_id = inc_resp.json()["id"]

    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.21, "lng": 91.81, "skills": ["rescue", "digging"],
    }, headers=auth_header(vol_token))
    vol_id = vol_resp.json()["id"]

    # Create assignment
    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol_id, "sla_minutes": 5,
    }, headers=auth_header(officer_token))
    assert assign_resp.status_code == 201
    assignment_id = assign_resp.json()["id"]

    # ACK assignment
    ack_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "acked"
    }, headers=auth_header(vol_token))
    assert ack_resp.status_code == 200

    # Done assignment
    done_resp = await client.patch(f"/assignments/{assignment_id}/status", json={
        "status": "done"
    }, headers=auth_header(vol_token))
    assert done_resp.status_code == 200

    # Check audit logs for all transitions
    async with TestSession() as db:
        result = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "Assignment",
                AuditLog.entity_id == assignment_id,
            )
        )
        logs = result.scalars().all()
        actions = [log.action for log in logs]
        assert "assign" in actions
        assert "status_acked" in actions
        assert "status_done" in actions

        ack_log = [l for l in logs if l.action == "status_acked"][0]
        assert ack_log.before["status"] == "pending"
        assert ack_log.after["status"] == "acked"

        done_log = [l for l in logs if l.action == "status_done"][0]
        assert done_log.before["status"] == "acked"
        assert done_log.after["status"] == "done"


@pytest.mark.asyncio
async def test_ack_prevents_auto_reassignment():
    """If assignment was ACKed within SLA, check_and_reassign_expired must NOT reassign it."""
    async with async_session() as db:
        user1 = User(phone="+919999999901", password_hash="x", name="Officer", role="officer", lang="en")
        user2 = User(phone="+919999999902", password_hash="x", name="Vol1", role="volunteer", lang="en")
        db.add_all([user1, user2])
        await db.flush()

        incident = Incident(
            reporter_id=user1.id, type="flood", description="test acked",
            lat=26.14, lng=91.73, severity=3, status="assigned",
        )
        db.add(incident)
        await db.flush()

        vol1 = Volunteer(user_id=user2.id, skills="rescue", lat=26.15, lng=91.74)
        db.add(vol1)
        await db.flush()

        assignment = Assignment(
            incident_id=incident.id,
            volunteer_id=vol1.id,
            status="acked",  # Already acknowledged
            acked_at=datetime.utcnow(),
            sla_deadline=datetime.utcnow() - timedelta(minutes=10),  # Expired past deadline
        )
        db.add(assignment)
        await db.commit()

    with patch("app.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
        await check_and_reassign_expired()

    async with async_session() as db:
        result = await db.execute(select(Assignment).where(Assignment.id == assignment.id))
        fresh_assignment = result.scalar_one()
        assert fresh_assignment.status == "acked"  # Unchanged!


@pytest.mark.asyncio
async def test_unacknowledged_past_sla_reassigns_to_different_volunteer():
    """Unacknowledged assignment past SLA deadline gets reassigned and excludes the timed-out volunteer."""
    async with async_session() as db:
        user1 = User(phone="+919999999911", password_hash="x", name="Officer", role="officer", lang="en")
        user2 = User(phone="+919999999912", password_hash="x", name="Vol1", role="volunteer", lang="en")
        user3 = User(phone="+919999999913", password_hash="x", name="Vol2", role="volunteer", lang="en")
        db.add_all([user1, user2, user3])
        await db.flush()

        incident = Incident(
            reporter_id=user1.id, type="flood", description="flood test",
            lat=26.14, lng=91.73, severity=3,
        )
        db.add(incident)
        await db.flush()

        # Vol1 is closer/better match, but is the one that timed out
        vol1 = Volunteer(user_id=user2.id, skills="swimming,rescue", lat=26.14, lng=91.73, availability_status="available")
        # Vol2 is another available volunteer
        vol2 = Volunteer(user_id=user3.id, skills="rescue", lat=26.15, lng=91.74, availability_status="available")
        db.add_all([vol1, vol2])
        await db.flush()

        old_assignment = Assignment(
            incident_id=incident.id, volunteer_id=vol1.id,
            status="pending",
            sla_deadline=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(old_assignment)
        await db.commit()

    with patch("app.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
        await check_and_reassign_expired()

    async with async_session() as db:
        result = await db.execute(select(Assignment).where(Assignment.incident_id == incident.id))
        assignments = result.scalars().all()
        assert len(assignments) == 2

        old = [a for a in assignments if a.id == old_assignment.id][0]
        assert old.status == "reassigned"

        new = [a for a in assignments if a.id != old_assignment.id][0]
        assert new.status == "pending"
        assert new.volunteer_id == vol2.id  # Selected vol2, not vol1!

        # Check audit log for reassignment
        audit_res = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_type == "Assignment",
                AuditLog.entity_id == old_assignment.id,
                AuditLog.action == "reassign"
            )
        )
        audit = audit_res.scalar_one_or_none()
        assert audit is not None
        assert audit.before["status"] == "pending"
        assert audit.after["status"] == "reassigned"
