"""Auto-reassign with exactly one new notification, no duplicates."""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

import pytest_asyncio

from app.background.auto_reassign import check_and_reassign_expired
from app.core.database import async_session, Base, engine
from app.models.user import User
from app.models.incident import Incident
from app.models.volunteer import Volunteer
from app.models.assignment import Assignment


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)



@pytest.mark.asyncio
async def test_auto_reassign_creates_exactly_one_new_assignment():
    async with async_session() as db:
        user1 = User(
            phone="+910000000001", password_hash="x", name="Officer",
            role="officer", lang="en",
        )
        user2 = User(
            phone="+910000000002", password_hash="x", name="Vol1",
            role="volunteer", lang="en",
        )
        user3 = User(
            phone="+910000000003", password_hash="x", name="Vol2",
            role="volunteer", lang="en",
        )
        db.add_all([user1, user2, user3])
        await db.flush()

        incident = Incident(
            reporter_id=user1.id, type="flood", description="test",
            lat=26.14, lng=91.73, severity=3,
        )
        db.add(incident)
        await db.flush()

        vol1 = Volunteer(
            user_id=user2.id, skills="rescue", lat=26.15, lng=91.74,
        )
        vol2 = Volunteer(
            user_id=user3.id, skills="rescue,swimming", lat=26.14, lng=91.73,
        )
        db.add_all([vol1, vol2])
        await db.flush()

        old_assignment = Assignment(
            incident_id=incident.id, volunteer_id=vol1.id,
            sla_deadline=datetime.utcnow() - timedelta(minutes=1),
        )
        db.add(old_assignment)
        await db.commit()

    with patch("app.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
        await check_and_reassign_expired()

    async with async_session() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(Assignment).where(Assignment.incident_id == incident.id)
        )
        assignments = result.scalars().all()

        old = [a for a in assignments if a.id == old_assignment.id]
        assert len(old) == 1
        assert old[0].status == "reassigned"

        new = [a for a in assignments if a.id != old_assignment.id]
        assert len(new) == 1
        assert new[0].status == "pending"
        # Ensure existing volunteer vol1 is NOT selected again; vol2 must be assigned
        assert new[0].volunteer_id == vol2.id

        inc_res = await db.execute(select(Incident).where(Incident.id == incident.id))
        inc = inc_res.scalar_one()
        assert inc.status == "assigned"


@pytest.mark.asyncio
async def test_auto_reassign_exhaustion_reverts_to_verified_with_audit_log():
    """
    When an expired assignment has NO replacement volunteer:
    1. Old assignment -> reassigned
    2. Incident -> verified (not left stranded as assigned with 0 active assignments)
    3. Exactly one audit log with action='reassign_exhausted' is created
    4. Zero active assignments remain
    """
    async with async_session() as db:
        user1 = User(
            phone="+910000000010", password_hash="x", name="Officer2",
            role="officer", lang="en",
        )
        user2 = User(
            phone="+910000000011", password_hash="x", name="SoleVol",
            role="volunteer", lang="en",
        )
        db.add_all([user1, user2])
        await db.flush()

        incident = Incident(
            reporter_id=user1.id, type="landslide", description="Solo vol test",
            lat=26.14, lng=91.73, severity=3, status="assigned",
        )
        db.add(incident)
        await db.flush()

        # Only ONE volunteer exists in database
        vol = Volunteer(
            user_id=user2.id, skills="rescue", lat=26.15, lng=91.74,
        )
        db.add(vol)
        await db.flush()

        # Expired assignment for the only volunteer
        old_assignment = Assignment(
            incident_id=incident.id, volunteer_id=vol.id,
            status="pending",
            sla_deadline=datetime.utcnow() - timedelta(minutes=2),
        )
        db.add(old_assignment)
        await db.commit()

    with patch("app.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
        await check_and_reassign_expired()

    async with async_session() as db:
        from sqlalchemy import select
        # 1. Check assignments: old must be 'reassigned', no new assignment invented
        assign_res = await db.execute(
            select(Assignment).where(Assignment.incident_id == incident.id)
        )
        all_assigns = assign_res.scalars().all()
        assert len(all_assigns) == 1
        assert all_assigns[0].id == old_assignment.id
        assert all_assigns[0].status == "reassigned"

        # 2. Check active assignments count: must be zero
        active_assigns = [a for a in all_assigns if a.status in ["pending", "acked", "in_progress"]]
        assert len(active_assigns) == 0

        # 3. Incident must NOT be stranded in 'assigned'; must be reverted to 'verified'
        inc_res = await db.execute(select(Incident).where(Incident.id == incident.id))
        inc = inc_res.scalar_one()
        assert inc.status == "verified"
        assert inc.status != "assigned"

        # 4. Check audit log for 'reassign_exhausted'
        from app.models.audit import AuditLog
        audit_res = await db.execute(
            select(AuditLog).where(
                AuditLog.entity_id == incident.id,
                AuditLog.action == "reassign_exhausted",
            )
        )
        exhaust_logs = audit_res.scalars().all()
        assert len(exhaust_logs) == 1
        log = exhaust_logs[0]
        assert log.before["status"] == "assigned"
        assert log.after["status"] == "verified"
        assert log.after["reason"] == "no_available_replacement_volunteers"


@pytest.mark.asyncio
async def test_auto_reassign_preserves_unrelated_active_and_acked_assignments():
    """
    Ensure unrelated assignments are untouched:
    - Non-expired pending assignment (deadline > now) remains pending
    - Already acked assignment (deadline < now, status == 'acked') remains acked
    """
    async with async_session() as db:
        user1 = User(
            phone="+910000000020", password_hash="x", name="Officer3",
            role="officer", lang="en",
        )
        user2 = User(
            phone="+910000000021", password_hash="x", name="VolActive",
            role="volunteer", lang="en",
        )
        user3 = User(
            phone="+910000000022", password_hash="x", name="VolAcked",
            role="volunteer", lang="en",
        )
        db.add_all([user1, user2, user3])
        await db.flush()

        incident1 = Incident(
            reporter_id=user1.id, type="flood", description="Preservation test 1",
            lat=26.14, lng=91.73, severity=3, status="assigned",
        )
        incident2 = Incident(
            reporter_id=user1.id, type="landslide", description="Preservation test 2",
            lat=26.15, lng=91.74, severity=2, status="assigned",
        )
        db.add_all([incident1, incident2])
        await db.flush()

        vol1 = Volunteer(user_id=user2.id, skills="rescue", lat=26.15, lng=91.74)
        vol2 = Volunteer(user_id=user3.id, skills="rescue", lat=26.16, lng=91.75)
        db.add_all([vol1, vol2])
        await db.flush()

        # Non-expired pending assignment for incident 1: deadline in future
        non_expired = Assignment(
            incident_id=incident1.id, volunteer_id=vol1.id,
            status="pending",
            sla_deadline=datetime.utcnow() + timedelta(minutes=10),
        )
        # Expired but already acked assignment for incident 2: status is acked
        already_acked = Assignment(
            incident_id=incident2.id, volunteer_id=vol2.id,
            status="acked",
            sla_deadline=datetime.utcnow() - timedelta(minutes=5),
            acked_at=datetime.utcnow() - timedelta(minutes=6),
        )
        db.add_all([non_expired, already_acked])
        await db.commit()

    with patch("app.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
        await check_and_reassign_expired()

    async with async_session() as db:
        from sqlalchemy import select
        res1 = (await db.execute(select(Assignment).where(Assignment.id == non_expired.id))).scalar_one()
        assert res1.status == "pending"

        res2 = (await db.execute(select(Assignment).where(Assignment.id == already_acked.id))).scalar_one()
        assert res2.status == "acked"
