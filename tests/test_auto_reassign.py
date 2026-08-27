"""Auto-reassign with exactly one new notification, no duplicates."""
import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from app.background.auto_reassign import check_and_reassign_expired
from app.core.database import async_session, Base, engine
from app.models.user import User
from app.models.incident import Incident
from app.models.volunteer import Volunteer
from app.models.assignment import Assignment


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
            user_id=user2.id, skills=["rescue"], lat=26.15, lng=91.74,
        )
        vol2 = Volunteer(
            user_id=user3.id, skills=["rescue", "swimming"], lat=26.14, lng=91.73,
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
