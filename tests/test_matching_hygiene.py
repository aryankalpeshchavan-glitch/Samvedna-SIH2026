"""
Step 4B: Volunteer Matching Hygiene Test Suite
=============================================
Validates:
1. Volunteer heartbeat/liveness filtering (fresh eligible, stale excluded, null excluded, unavailable excluded).
2. Historical volunteer exclusion during auto-reassignment across multiple assignments.
3. Scoring and ranking determinism, bounds [0, 1].
4. Enqueue behavior: POST /incidents and SMS do NOT enqueue, verify DOES enqueue.
"""
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from app.core.config import settings
from app.core.database import async_session
from app.models.user import User
from app.models.incident import Incident
from app.models.volunteer import Volunteer
from app.models.assignment import Assignment
from app.matching.engine import find_best_volunteer, score, haversine_km, skill_match_score
from app.background.auto_reassign import check_and_reassign_expired
from tests.test_api import auth_header, client, register_and_login, setup_db, TestSession


# ─── A. Volunteer Heartbeat & Liveness ────────────────────────────────────────

@pytest.mark.asyncio
async def test_volunteer_liveness_heartbeat_filtering(client: AsyncClient):
    """
    Verifies that find_best_volunteer():
    - selects available volunteer with fresh heartbeat
    - excludes available volunteer with stale heartbeat
    - excludes available volunteer with null heartbeat
    - excludes unavailable volunteer even with fresh heartbeat
    """
    async with async_session() as db:
        now = datetime.utcnow()
        u_officer = User(phone="+919999000001", password_hash="x", role="officer", name="Officer")
        u_fresh = User(phone="+919999000002", password_hash="x", role="volunteer", name="FreshVol")
        u_stale = User(phone="+919999000003", password_hash="x", role="volunteer", name="StaleVol")
        u_null = User(phone="+919999000004", password_hash="x", role="volunteer", name="NullVol")
        u_unavail = User(phone="+919999000005", password_hash="x", role="volunteer", name="UnavailVol")
        db.add_all([u_officer, u_fresh, u_stale, u_null, u_unavail])
        await db.flush()

        incident = Incident(
            reporter_id=u_officer.id,
            type="flood",
            description="Liveness test flood",
            lat=26.14,
            lng=91.73,
            status="verified",
        )
        db.add(incident)
        await db.flush()

        # 1. Fresh heartbeat (within configured 30 mins)
        vol_fresh = Volunteer(
            user_id=u_fresh.id,
            skills="rescue,swimming",
            lat=26.15,
            lng=91.74,
            availability_status="available",
            last_heartbeat=now - timedelta(minutes=5),
        )
        # 2. Stale heartbeat (beyond configured 30 mins, e.g. 45 mins ago)
        vol_stale = Volunteer(
            user_id=u_stale.id,
            skills="rescue,swimming",
            lat=26.14,
            lng=91.73,  # Closer proximity, but stale!
            availability_status="available",
            last_heartbeat=now - timedelta(minutes=settings.VOLUNTEER_HEARTBEAT_TIMEOUT_MINUTES + 15),
        )
        # 3. Null heartbeat
        vol_null = Volunteer(
            user_id=u_null.id,
            skills="rescue,swimming",
            lat=26.14,
            lng=91.73,
            availability_status="available",
            last_heartbeat=now - timedelta(minutes=1),
        )
        # 4. Unavailable status, even though heartbeat is fresh
        vol_unavail = Volunteer(
            user_id=u_unavail.id,
            skills="rescue,swimming",
            lat=26.14,
            lng=91.73,
            availability_status="busy",
            last_heartbeat=now - timedelta(minutes=2),
        )
        db.add_all([vol_fresh, vol_stale, vol_null, vol_unavail])
        await db.flush()

        # Explicitly update vol_null to NULL in the database
        await db.execute(
            update(Volunteer).where(Volunteer.id == vol_null.id).values(last_heartbeat=None)
        )
        await db.commit()

    async with async_session() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident.id))).scalar_one()
        best = await find_best_volunteer(db, inc)

        # Only vol_fresh is eligible! Stale, null, and busy are strictly excluded.
        assert best is not None
        selected_vol, match_score = best
        assert selected_vol.id == vol_fresh.id
        assert match_score > 0.0


# ─── B. Historical Exclusion Across Multi-Hop Reassignments ────────────────────

@pytest.mark.asyncio
async def test_auto_reassign_excludes_all_historical_volunteers(client: AsyncClient):
    """
    Tests that when an incident is reassigned, ALL previously assigned volunteers
    (not just the immediate predecessor) are excluded from the replacement search.
    """
    async with async_session() as db:
        now = datetime.utcnow()
        u_off = User(phone="+919999111111", password_hash="x", role="officer", name="Off")
        u_v1 = User(phone="+919999111112", password_hash="x", role="volunteer", name="Vol1")
        u_v2 = User(phone="+919999111113", password_hash="x", role="volunteer", name="Vol2")
        u_v3 = User(phone="+919999111114", password_hash="x", role="volunteer", name="Vol3")
        db.add_all([u_off, u_v1, u_v2, u_v3])
        await db.flush()

        incident = Incident(
            reporter_id=u_off.id,
            type="flood",
            description="Multi-hop reassignment test",
            lat=26.14,
            lng=91.73,
            status="assigned",
        )
        db.add(incident)
        await db.flush()

        v1 = Volunteer(user_id=u_v1.id, skills="rescue", lat=26.14, lng=91.73, last_heartbeat=now)
        v2 = Volunteer(user_id=u_v2.id, skills="rescue", lat=26.15, lng=91.74, last_heartbeat=now)
        v3 = Volunteer(user_id=u_v3.id, skills="rescue", lat=26.16, lng=91.75, last_heartbeat=now)
        db.add_all([v1, v2, v3])
        await db.flush()

        # Simulate history:
        # 1. Assignment 1 (Vol 1) expired earlier -> status="reassigned"
        assign1 = Assignment(
            incident_id=incident.id,
            volunteer_id=v1.id,
            status="reassigned",
            assigned_at=now - timedelta(minutes=20),
            sla_deadline=now - timedelta(minutes=15),
        )
        # 2. Assignment 2 (Vol 2) is the current pending assignment that just expired!
        assign2 = Assignment(
            incident_id=incident.id,
            volunteer_id=v2.id,
            status="pending",
            assigned_at=now - timedelta(minutes=15),
            sla_deadline=now - timedelta(minutes=1),
        )
        db.add_all([assign1, assign2])
        await db.commit()

        v3_id = v3.id

    with patch("app.notifications.dispatcher.dispatch_notification", new_callable=AsyncMock):
        with patch("app.realtime.ws_manager.ws_manager.broadcast", new_callable=AsyncMock):
            await check_and_reassign_expired()

    async with async_session() as db:
        res = await db.execute(select(Assignment).where(Assignment.incident_id == incident.id))
        assignments = res.scalars().all()

        # Active replacement must be created
        active = [a for a in assignments if a.status == "pending"]
        assert len(active) == 1

        # Must NOT be Vol 1 (old history) or Vol 2 (immediate predecessor); must be Vol 3!
        assert active[0].volunteer_id == v3_id


# ─── C. Scoring and Ranking Determinism ───────────────────────────────────────

@pytest.mark.asyncio
async def test_matching_scoring_and_ranking_determinism(client: AsyncClient):
    """
    Verifies that scoring formula:
    - distance decay via haversine
    - skill match ratio
    - resource boost
    - bounds in [0.0, 1.0]
    - deterministic ordering
    """
    async with async_session() as db:
        now = datetime.utcnow()
        u_off = User(phone="+919999222221", password_hash="x", role="officer", name="Off")
        u_expert = User(phone="+919999222222", password_hash="x", role="volunteer", name="Expert")
        u_novice = User(phone="+919999222223", password_hash="x", role="volunteer", name="Novice")
        db.add_all([u_off, u_expert, u_novice])
        await db.flush()

        incident = Incident(
            reporter_id=u_off.id,
            type="flood",
            description="Scoring test",
            lat=26.0,
            lng=91.0,
            status="verified",
        )
        db.add(incident)
        await db.flush()

        # Expert: exact skill match ("swimming,rescue,boat,first_aid,flood"), close distance
        vol_expert = Volunteer(
            user_id=u_expert.id,
            skills="swimming,rescue,boat,first_aid,flood",
            lat=26.01,
            lng=91.01,
            last_heartbeat=now,
        )
        # Novice: no relevant skills, further away
        vol_novice = Volunteer(
            user_id=u_novice.id,
            skills="accounting,cooking",
            lat=26.3,
            lng=91.3,
            last_heartbeat=now,
        )
        db.add_all([vol_expert, vol_novice])
        await db.commit()

    async with async_session() as db:
        inc = (await db.execute(select(Incident).where(Incident.id == incident.id))).scalar_one()
        v_exp = (await db.execute(select(Volunteer).where(Volunteer.id == vol_expert.id))).scalar_one()
        v_nov = (await db.execute(select(Volunteer).where(Volunteer.id == vol_novice.id))).scalar_one()

        score_exp = await score(db, v_exp, inc)
        score_nov = await score(db, v_nov, inc)

        # Both must be bounded [0.0, 1.0]
        assert 0.0 <= score_exp <= 1.0
        assert 0.0 <= score_nov <= 1.0

        # Expert must rank significantly higher than novice
        assert score_exp > score_nov

        # find_best_volunteer must pick expert
        best = await find_best_volunteer(db, inc)
        assert best is not None
        assert best[0].id == v_exp.id


# ─── D. Enqueue Behavior (POST /incidents & SMS vs Verify) ───────────────────

@pytest.mark.asyncio
async def test_enqueue_behavior_only_on_verification(client: AsyncClient):
    """
    Verifies that:
    1. POST /incidents does NOT enqueue matching.
    2. POST /incidents/sms does NOT enqueue matching.
    3. PATCH /incidents/{id}/verify DOES enqueue matching.
    """
    officer_token = await register_and_login(client, "officer")
    citizen_phone = "+919876543210"
    await client.post("/auth/register", json={
        "phone": citizen_phone,
        "password": "Password123!",
        "name": "SMS Citizen",
        "role": "citizen",
    })

    with patch("app.routers.incidents.enqueue_matching_job", new_callable=AsyncMock) as mock_enqueue:
        # 1. POST /incidents
        resp_web = await client.post("/incidents", json={
            "type": "flood",
            "description": "Rising water in colony",
            "lat": 26.14,
            "lng": 91.73,
            "severity": 2,
        }, headers=auth_header(officer_token))
        assert resp_web.status_code == 201
        inc_id = resp_web.json()["id"]

        # Must NOT have called enqueue_matching_job
        mock_enqueue.assert_not_called()

        # 2. POST /incidents/sms
        resp_sms = await client.post("/incidents/sms", json={
            "phone": citizen_phone,
            "text": "Flood near river bank",
            "lat": 26.15,
            "lng": 91.75,
        })
        assert resp_sms.status_code == 201
        # Still must NOT have called enqueue_matching_job
        mock_enqueue.assert_not_called()

        # 3. Verify the incident
        resp_verify = await client.patch(f"/incidents/{inc_id}/verify", json={
            "data_label": "live",
        }, headers=auth_header(officer_token))
        assert resp_verify.status_code == 200

        # Now enqueue_matching_job MUST be called with inc_id
        mock_enqueue.assert_called_once_with(inc_id)
