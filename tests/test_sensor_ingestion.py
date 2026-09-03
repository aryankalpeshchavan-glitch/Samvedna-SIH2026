"""
Step 3: Sensor Ingestion & Heartbeat Test Suite
===============================================
Validates sensor registration, telemetry ingestion, validation rules,
idempotency, DB uniqueness constraints, heartbeat, health classification,
and provenance tracking.
"""
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.models.sensor import Sensor, SensorReading
from app.services.sensor_health import compute_sensor_health
from tests.test_api import auth_header, client, register_and_login, setup_db, TestSession


# ─── 1. Sensor Registration Succeeds for Officer/Admin ────────────────────────

@pytest.mark.asyncio
async def test_sensor_registration_succeeds_for_officer(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    resp = await client.post("/sensors/register", json={
        "id": "SNS-TEST-01",
        "name": "Guwahati Ridge Station",
        "sensor_type": "hydro_station",
        "lat": 26.14,
        "lng": 91.73,
        "district": "Kamrup Metropolitan",
        "state": "Assam",
        "is_active": True,
        "data_label": "live",
    }, headers=auth_header(officer_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == "SNS-TEST-01"
    assert data["name"] == "Guwahati Ridge Station"
    assert data["sensor_type"] == "hydro_station"
    assert data["health"] == "OFFLINE"  # Newly created sensor with no last_seen is OFFLINE
    assert data["data_label"] == "live"


# ─── 2. Citizen / Volunteer Cannot Register Sensors ───────────────────────────

@pytest.mark.asyncio
async def test_citizen_and_volunteer_cannot_register_sensor(client: AsyncClient):
    citizen_token = await register_and_login(client, "citizen")
    vol_token = await register_and_login(client, "volunteer")

    payload = {
        "id": "SNS-UNAUTH-01",
        "name": "Unauthorized Station",
        "sensor_type": "rain_gauge",
        "lat": 26.15,
        "lng": 91.75,
    }

    c_resp = await client.post("/sensors/register", json=payload, headers=auth_header(citizen_token))
    assert c_resp.status_code == 403

    v_resp = await client.post("/sensors/register", json=payload, headers=auth_header(vol_token))
    assert v_resp.status_code == 403


# ─── 3. Duplicate Sensor Registration is Rejected ─────────────────────────────

@pytest.mark.asyncio
async def test_duplicate_sensor_registration_rejected(client: AsyncClient):
    admin_token = await register_and_login(client, "admin")

    payload = {
        "id": "SNS-DUP-01",
        "name": "Aizawl North Slope",
        "sensor_type": "tiltmeter",
        "lat": 23.73,
        "lng": 92.71,
    }

    resp1 = await client.post("/sensors/register", json=payload, headers=auth_header(admin_token))
    assert resp1.status_code == 201

    resp2 = await client.post("/sensors/register", json=payload, headers=auth_header(admin_token))
    assert resp2.status_code == 400
    assert "already exists" in resp2.text


# ─── 4. Valid Telemetry Ingestion Creates Exactly One Reading ─────────────────

@pytest.mark.asyncio
async def test_valid_telemetry_ingestion_creates_one_reading(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-VALID-01",
        "name": "Cherrapunji Station",
        "sensor_type": "hydro_station",
        "lat": 25.27,
        "lng": 91.73,
    }, headers=auth_header(officer_token))

    obs_time = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": obs_time,
        "rainfall_mm": 42.5,
        "soil_moisture_pct": 78.0,
        "tilt_degrees": 2.4,
        "temperature_c": 22.0,
        "battery_pct": 95.0,
        "data_label": "live",
    }, headers=auth_header(officer_token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["sensor_id"] == "SNS-VALID-01"
    assert data["rainfall_mm"] == 42.5
    assert data["soil_moisture_pct"] == 78.0
    assert data["data_label"] == "live"

    # Verify exactly one reading in database
    async with TestSession() as db:
        res = await db.execute(select(SensorReading).where(SensorReading.sensor_id == "SNS-VALID-01"))
        readings = res.scalars().all()
        assert len(readings) == 1


# ─── 5. Unknown Sensor Cannot Ingest ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_unknown_sensor_cannot_ingest(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-NONEXISTENT",
        "timestamp": datetime.utcnow().isoformat(),
        "rainfall_mm": 10.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 404
    assert "not found" in resp.text


# ─── 6. Inactive Sensor Cannot Ingest ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_inactive_sensor_cannot_ingest(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-INACTIVE-01",
        "name": "Decommissioned Station",
        "sensor_type": "rain_gauge",
        "lat": 26.1,
        "lng": 91.7,
        "is_active": False,
    }, headers=auth_header(officer_token))

    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-INACTIVE-01",
        "timestamp": datetime.utcnow().isoformat(),
        "rainfall_mm": 5.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 400
    assert "inactive" in resp.text


# ─── 7. Negative Rainfall Rejected ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_negative_rainfall_rejected(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": datetime.utcnow().isoformat(),
        "rainfall_mm": -5.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 422


# ─── 8. Soil Moisture > 100 Rejected ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_soil_moisture_over_100_rejected(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": datetime.utcnow().isoformat(),
        "soil_moisture_pct": 105.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 422


# ─── 9. Battery > 100 Rejected ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_battery_over_100_rejected(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": datetime.utcnow().isoformat(),
        "battery_pct": 150.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 422


# ─── 10. NaN / Infinite Numeric Payloads Rejected ─────────────────────────────

@pytest.mark.asyncio
async def test_nan_and_infinite_payloads_rejected(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    resp_inf = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": datetime.utcnow().isoformat(),
        "rainfall_mm": "Infinity",
    }, headers=auth_header(officer_token))
    assert resp_inf.status_code == 422

    resp_nan = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": datetime.utcnow().isoformat(),
        "tilt_degrees": "NaN",
    }, headers=auth_header(officer_token))
    assert resp_nan.status_code == 422


# ─── 11. Future Timestamp Rejected ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_future_timestamp_rejected(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    future_time = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-VALID-01",
        "timestamp": future_time,
        "rainfall_mm": 12.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 422
    assert "future" in resp.text.lower()


# ─── 12. Duplicate (sensor_id, timestamp) is Idempotent ───────────────────────

@pytest.mark.asyncio
async def test_duplicate_ingestion_is_idempotent(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-IDEMP-01",
        "name": "Idempotent Station",
        "sensor_type": "hydro_station",
        "lat": 26.2,
        "lng": 91.8,
    }, headers=auth_header(officer_token))

    fixed_timestamp = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
    payload = {
        "sensor_id": "SNS-IDEMP-01",
        "timestamp": fixed_timestamp,
        "rainfall_mm": 18.2,
        "soil_moisture_pct": 65.0,
    }

    # 1. First submission succeeds with 201
    resp1 = await client.post("/sensors/ingest", json=payload, headers=auth_header(officer_token))
    assert resp1.status_code == 201
    reading_id_1 = resp1.json()["id"]

    # 2. Duplicate submission returns clean HTTP 200 with existing reading
    resp2 = await client.post("/sensors/ingest", json=payload, headers=auth_header(officer_token))
    assert resp2.status_code == 200
    reading_id_2 = resp2.json()["id"]
    assert reading_id_1 == reading_id_2

    # 3. Exactly one reading remains in database
    async with TestSession() as db:
        res = await db.execute(select(SensorReading).where(SensorReading.sensor_id == "SNS-IDEMP-01"))
        all_readings = res.scalars().all()
        assert len(all_readings) == 1


# ─── 13. Database Uniqueness Constraint is Enforced ───────────────────────────

@pytest.mark.asyncio
async def test_database_uniqueness_constraint_enforced():
    """
    Directly attempt to flush two SensorReading instances with identical (sensor_id, timestamp).
    The DB UniqueConstraint('sensor_id', 'timestamp') must raise IntegrityError.
    """
    async with TestSession() as db:
        sensor = Sensor(
            id="SNS-DB-UNIQUE",
            name="Unique Test Sensor",
            sensor_type="rain_gauge",
            lat=26.0,
            lng=91.0,
            created_at=datetime.utcnow(),
        )
        db.add(sensor)
        await db.flush()

        fixed_time = datetime(2026, 9, 3, 12, 0, 0)
        r1 = SensorReading(
            sensor_id="SNS-DB-UNIQUE",
            timestamp=fixed_time,
            rainfall_mm=10.0,
            created_at=datetime.utcnow(),
        )
        db.add(r1)
        await db.flush()

        r2 = SensorReading(
            sensor_id="SNS-DB-UNIQUE",
            timestamp=fixed_time,
            rainfall_mm=20.0,
            created_at=datetime.utcnow(),
        )
        db.add(r2)

        with pytest.raises(IntegrityError):
            await db.flush()

        await db.rollback()


# ─── 14. Successful Ingestion Updates sensor.last_seen ────────────────────────

@pytest.mark.asyncio
async def test_ingestion_updates_sensor_last_seen(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-LIVENESS-01",
        "name": "Liveness Sensor",
        "sensor_type": "hydro_station",
        "lat": 26.5,
        "lng": 91.5,
    }, headers=auth_header(officer_token))

    # Before ingestion: last_seen is None
    async with TestSession() as db:
        s = (await db.execute(select(Sensor).where(Sensor.id == "SNS-LIVENESS-01"))).scalar_one()
        assert s.last_seen is None

    before_ingest = datetime.utcnow() - timedelta(seconds=1)
    await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-LIVENESS-01",
        "timestamp": (datetime.utcnow() - timedelta(minutes=10)).isoformat(),
        "rainfall_mm": 5.0,
    }, headers=auth_header(officer_token))

    # After ingestion: sensor.last_seen must be updated to backend receipt time
    async with TestSession() as db:
        s = (await db.execute(select(Sensor).where(Sensor.id == "SNS-LIVENESS-01"))).scalar_one()
        assert s.last_seen is not None
        assert s.last_seen >= before_ingest


# ─── 15. Heartbeat Updates last_seen ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_heartbeat_updates_last_seen(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-HB-01",
        "name": "Heartbeat Sensor",
        "sensor_type": "tiltmeter",
        "lat": 27.0,
        "lng": 92.0,
    }, headers=auth_header(officer_token))

    before_hb = datetime.utcnow() - timedelta(seconds=1)
    resp = await client.post("/sensors/SNS-HB-01/heartbeat", json={
        "battery_pct": 88.0,
    }, headers=auth_header(officer_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["health"] == "ONLINE"
    assert data["last_seen"] is not None

    async with TestSession() as db:
        s = (await db.execute(select(Sensor).where(Sensor.id == "SNS-HB-01"))).scalar_one()
        assert s.last_seen >= before_hb


# ─── 16. Health Classification (ONLINE, STALE, OFFLINE) ───────────────────────

def test_sensor_health_classification():
    now = datetime.utcnow()

    # 1. No last_seen -> OFFLINE
    assert compute_sensor_health(None, now=now) == "OFFLINE"

    # 2. Recent (e.g. 1 minute ago <= SENSOR_STALE_TIMEOUT_SECONDS=300) -> ONLINE
    recent = now - timedelta(minutes=1)
    assert compute_sensor_health(recent, now=now) == "ONLINE"

    # 3. Between stale (300s) and offline (1800s), e.g. 10 minutes ago -> STALE
    stale_time = now - timedelta(minutes=10)
    assert compute_sensor_health(stale_time, now=now) == "STALE"

    # 4. Beyond offline threshold (e.g. 45 minutes ago) -> OFFLINE
    offline_time = now - timedelta(minutes=45)
    assert compute_sensor_health(offline_time, now=now) == "OFFLINE"


# ─── 17. Telemetry Provenance is Preserved ────────────────────────────────────

@pytest.mark.asyncio
async def test_telemetry_provenance_preserved(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-PROV-01",
        "name": "Provenance Station",
        "sensor_type": "hydro_station",
        "lat": 26.1,
        "lng": 91.7,
        "data_label": "live",
    }, headers=auth_header(officer_token))

    # Ingest reading with explicit simulated label
    resp = await client.post("/sensors/ingest", json={
        "sensor_id": "SNS-PROV-01",
        "timestamp": (datetime.utcnow() - timedelta(minutes=2)).isoformat(),
        "rainfall_mm": 15.0,
        "data_label": "simulated",
    }, headers=auth_header(officer_token))
    assert resp.status_code == 201
    assert resp.json()["data_label"] == "simulated"

    async with TestSession() as db:
        reading = (await db.execute(select(SensorReading).where(SensorReading.sensor_id == "SNS-PROV-01"))).scalar_one()
        assert reading.data_label == "simulated"


# ─── 18. Sensor History Endpoint is Bounded and Returns Readings ───────────────

@pytest.mark.asyncio
async def test_sensor_history_endpoint_bounded(client: AsyncClient):
    officer_token = await register_and_login(client, "officer")

    await client.post("/sensors/register", json={
        "id": "SNS-HIST-01",
        "name": "History Station",
        "sensor_type": "hydro_station",
        "lat": 26.1,
        "lng": 91.7,
    }, headers=auth_header(officer_token))

    # Ingest 5 readings
    for i in range(5):
        obs_time = (datetime.utcnow() - timedelta(minutes=10 + i * 5)).isoformat()
        await client.post("/sensors/ingest", json={
            "sensor_id": "SNS-HIST-01",
            "timestamp": obs_time,
            "rainfall_mm": float(i * 10),
        }, headers=auth_header(officer_token))

    # Query history with limit=3
    resp = await client.get("/sensors/SNS-HIST-01/readings?limit=3", headers=auth_header(officer_token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 3
    # Check ordering: newest first
    assert data[0]["rainfall_mm"] == 0.0  # minutes=10 is newer than minutes=15 (rainfall 10.0)
    assert data[1]["rainfall_mm"] == 10.0
    assert data[2]["rainfall_mm"] == 20.0
