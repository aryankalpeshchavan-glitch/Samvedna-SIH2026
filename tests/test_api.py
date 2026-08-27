import asyncio
import httpx
import json
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://crisiscore:crisiscore@localhost:5432/crisiscore_test"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, pool_pre_ping=True)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
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


# ─── AUTH TESTS ───

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    phone = f"+91{uuid.uuid4().int % 10**10:010d}"
    resp = await client.post("/auth/register", json={
        "phone": phone, "password": "pass123", "name": "A", "role": "citizen"
    })
    assert resp.status_code == 201

    resp = await client.post("/auth/login", json={"phone": phone, "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    phone = f"+91{uuid.uuid4().int % 10**10:010d}"
    await client.post("/auth/register", json={
        "phone": phone, "password": "pass123", "name": "B", "role": "citizen"
    })
    resp = await client.post("/auth/login", json={"phone": phone, "password": "wrong"})
    assert resp.status_code == 401


# ─── HEALTH TEST ───

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("healthy", "degraded")


# ─── INCIDENT FLOW ───

@pytest.mark.asyncio
async def test_incident_create_verify_flow(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    resp = await client.post("/incidents", json={
        "type": "flood", "description": "River rising fast",
        "lat": 26.1445, "lng": 91.7362, "severity": 4,
    }, headers=auth_header(citizen_token))
    assert resp.status_code == 201
    incident = resp.json()
    incident_id = incident["id"]

    resp = await client.get(f"/incidents/{incident_id}", headers=auth_header(citizen_token))
    assert resp.status_code == 200

    resp = await client.patch(f"/incidents/{incident_id}/verify",
        json={"data_label": "live"}, headers=auth_header(officer_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "verified"


@pytest.mark.asyncio
async def test_cannot_verify_as_citizen(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    resp = await client.post("/incidents", json={
        "type": "fire", "description": "Building fire",
        "lat": 26.0, "lng": 91.0, "severity": 3,
    }, headers=auth_header(citizen_token))
    incident_id = resp.json()["id"]

    resp = await client.patch(f"/incidents/{incident_id}/verify",
        json={"data_label": "synthetic"}, headers=auth_header(citizen_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_idempotency_key(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    key = str(uuid.uuid4())

    resp1 = await client.post("/incidents", json={
        "type": "flood", "description": "test",
        "lat": 26.0, "lng": 91.0, "severity": 2, "idempotency_key": key,
    }, headers=auth_header(citizen_token))
    resp2 = await client.post("/incidents", json={
        "type": "flood", "description": "test duplicate",
        "lat": 26.0, "lng": 91.0, "severity": 2, "idempotency_key": key,
    }, headers=auth_header(citizen_token))
    assert resp1.json()["id"] == resp2.json()["id"]


# ─── VOLUNTEER HEARTBEAT ───

@pytest.mark.asyncio
async def test_volunteer_heartbeat(client: AsyncClient):
    token = await register_and_login(client, "volunteer")
    resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.1445, "lng": 91.7362, "availability_status": "available",
        "skills": ["rescue", "swimming"],
    }, headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["skills"] == ["rescue", "swimming"]


# ─── ASSIGNMENT + AUTO REASSIGN ───

@pytest.mark.asyncio
async def test_assignment_lifecycle(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_token = await register_and_login(client, "volunteer")

    inc_resp = await client.post("/incidents", json={
        "type": "landslide", "description": "Road blocked",
        "lat": 26.2, "lng": 91.8, "severity": 3,
    }, headers=auth_header(citizen_token))
    incident_id = inc_resp.json()["id"]

    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.21, "lng": 91.81, "skills": ["rescue"],
    }, headers=auth_header(vol_token))
    vol_id = vol_resp.json()["id"]

    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol_id,
    }, headers=auth_header(officer_token))
    assert assign_resp.status_code == 201
    assignment_id = assign_resp.json()["id"]

    ack_resp = await client.patch(f"/assignments/{assignment_id}/status",
        json={"status": "acked"}, headers=auth_header(vol_token))
    assert ack_resp.json()["status"] == "acked"

    progress_resp = await client.patch(f"/assignments/{assignment_id}/status",
        json={"status": "in_progress"}, headers=auth_header(vol_token))
    assert progress_resp.json()["status"] == "in_progress"

    done_resp = await client.patch(f"/assignments/{assignment_id}/status",
        json={"status": "done"}, headers=auth_header(vol_token))
    assert done_resp.json()["status"] == "done"


# ─── MESH SIMULATE ───

@pytest.mark.asyncio
async def test_mesh_simulate(client: AsyncClient):
    token = await register_and_login(client, "citizen")
    resp = await client.post("/mesh/simulate", json={
        "origin_device_id": "device_001",
        "payload": {"msg": "help needed"},
        "data_label": "synthetic",
    }, headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["hops_completed"] == 2
    assert len(data["relay_path"]) == 3


# ─── RISK ENDPOINT ───

@pytest.mark.asyncio
async def test_risk_empty(client: AsyncClient):
    token = await register_and_login(client, "citizen")
    resp = await client.get("/risk?bbox=25,90,27,92&horizon=24h",
        headers=auth_header(token))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ─── STATUS POLLING ───

@pytest.mark.asyncio
async def test_status_polling(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    resp = await client.post("/incidents", json={
        "type": "fire", "description": "Bush fire",
        "lat": 26.3, "lng": 91.9, "severity": 5,
    }, headers=auth_header(citizen_token))
    incident_id = resp.json()["id"]

    status_resp = await client.get(f"/status/{incident_id}",
        headers=auth_header(citizen_token))
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "reported"
