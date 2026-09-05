import asyncio
import os
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.core.database import Base, get_db, engine
from app.models.incident import Incident
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./test_crisiscore.db"),
)

connect_args = {}
if "sqlite" in TEST_DATABASE_URL:
    connect_args["check_same_thread"] = False

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True if "sqlite" not in TEST_DATABASE_URL else False,
    connect_args=connect_args,
)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def register_and_login(client: AsyncClient, role: str = "citizen") -> str:
    phone = f"+91{uuid.uuid4().int % 10**10:010d}"
    await client.post("/auth/register", json={
        "phone": phone,
        "password": "testpass123",
        "name": f"Test User {role}",
        "role": role,
    })
    resp = await client.post("/auth/login", json={
        "phone": phone,
        "password": "testpass123",
    })
    return resp.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── DAY 2 OFFLINE SYNC TESTS ───

@pytest.mark.asyncio
async def test_offline_incident_capture_timestamp_preserved(client: AsyncClient):
    token = await register_and_login(client, "citizen")
    offline_occurred = (datetime.utcnow() - timedelta(hours=3)).isoformat()
    key = str(uuid.uuid4())

    resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Flash flood captured offline earlier",
        "lat": 26.14,
        "lng": 91.73,
        "severity": 4,
        "idempotency_key": key,
        "occurred_at": offline_occurred,
        "data_label": "replayed",
    }, headers=auth_header(token))

    assert resp.status_code == 201
    data = resp.json()
    assert data["data_label"] == "replayed"
    assert data["occurred_at"] is not None
    # Verify occurred_at matches the earlier offline capture timestamp
    assert data["occurred_at"].startswith(offline_occurred[:16])


@pytest.mark.asyncio
async def test_offline_idempotency_deduplication(client: AsyncClient):
    token = await register_and_login(client, "citizen")
    key = str(uuid.uuid4())
    offline_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()

    payload = {
        "type": "landslide",
        "description": "Mudslide on Highway 27",
        "lat": 26.20,
        "lng": 91.80,
        "severity": 3,
        "idempotency_key": key,
        "occurred_at": offline_time,
        "data_label": "replayed",
    }

    # First sync
    resp1 = await client.post("/incidents", json=payload, headers=auth_header(token))
    assert resp1.status_code == 201
    inc1 = resp1.json()

    # Replayed sync of the exact same offline report
    resp2 = await client.post("/incidents", json=payload, headers=auth_header(token))
    assert resp2.status_code == 201
    inc2 = resp2.json()

    assert inc1["id"] == inc2["id"]
    assert inc2["data_label"] == "replayed"


@pytest.mark.asyncio
async def test_batch_sync_multiple_new_incidents(client: AsyncClient):
    token = await register_and_login(client, "citizen")

    items = [
        {
            "type": "flood",
            "description": f"Offline report {i}",
            "lat": 26.10 + i * 0.01,
            "lng": 91.70 + i * 0.01,
            "severity": 2,
            "idempotency_key": str(uuid.uuid4()),
            "data_label": "replayed",
            "occurred_at": (datetime.utcnow() - timedelta(minutes=30 * i)).isoformat(),
        }
        for i in range(3)
    ]

    resp = await client.post("/incidents/sync", json={"items": items}, headers=auth_header(token))
    assert resp.status_code == 200
    result = resp.json()

    assert len(result["synced"]) == 3
    assert len(result["duplicates"]) == 0
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_batch_sync_mixed_new_and_duplicate_incidents(client: AsyncClient):
    token = await register_and_login(client, "citizen")

    key_existing = str(uuid.uuid4())
    # Pre-sync one incident
    pre_resp = await client.post("/incidents", json={
        "type": "fire",
        "description": "Pre-existing fire incident",
        "lat": 26.15,
        "lng": 91.75,
        "severity": 3,
        "idempotency_key": key_existing,
        "data_label": "live",
    }, headers=auth_header(token))
    pre_id = pre_resp.json()["id"]

    key_new1 = str(uuid.uuid4())
    key_new2 = str(uuid.uuid4())

    batch_items = [
        {
            "type": "fire",
            "description": "Re-sent fire incident",
            "lat": 26.15,
            "lng": 91.75,
            "severity": 3,
            "idempotency_key": key_existing,
            "data_label": "replayed",
        },
        {
            "type": "flood",
            "description": "New flood incident 1",
            "lat": 26.16,
            "lng": 91.76,
            "severity": 2,
            "idempotency_key": key_new1,
            "data_label": "replayed",
        },
        {
            "type": "landslide",
            "description": "New landslide incident 2",
            "lat": 26.17,
            "lng": 91.77,
            "severity": 4,
            "idempotency_key": key_new2,
            "data_label": "replayed",
        },
    ]

    resp = await client.post("/incidents/sync", json={"items": batch_items}, headers=auth_header(token))
    assert resp.status_code == 200
    result = resp.json()

    assert len(result["synced"]) == 2
    assert len(result["duplicates"]) == 1
    assert result["duplicates"][0]["id"] == pre_id
    assert len(result["errors"]) == 0


@pytest.mark.asyncio
async def test_state_conflict_protection(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    key = str(uuid.uuid4())

    # 1. Citizen creates incident
    create_resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Flood near bridge",
        "lat": 26.14,
        "lng": 91.73,
        "severity": 3,
        "idempotency_key": key,
    }, headers=auth_header(citizen_token))
    incident_id = create_resp.json()["id"]

    # 2. Officer verifies the incident
    verify_resp = await client.patch(f"/incidents/{incident_id}/verify", json={
        "data_label": "live",
    }, headers=auth_header(officer_token))
    assert verify_resp.json()["status"] == "verified"

    # 3. Offline client attempts to sync original report again
    replay_resp = await client.post("/incidents", json={
        "type": "flood",
        "description": "Flood near bridge",
        "lat": 26.14,
        "lng": 91.73,
        "severity": 3,
        "idempotency_key": key,
    }, headers=auth_header(citizen_token))

    # Must return existing verified state, not reset to "reported"
    assert replay_resp.status_code == 201
    assert replay_resp.json()["id"] == incident_id
    assert replay_resp.json()["status"] == "verified"
