"""
Sensor Ingestion & Heartbeat Router
===================================
Endpoints for:
- Registering physical/virtual sensors (officer/admin)
- Ingesting telemetry observations with duplicate protection
- Liveness heartbeat tracking
- Listing sensors with dynamic health status (ONLINE, STALE, OFFLINE)
- Querying recent observation history
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.user import User
from app.models.sensor import Sensor, SensorReading
from app.schemas.sensor import (
    SensorRegisterCreate, SensorReadingCreate, SensorHeartbeat,
    SensorOut, SensorReadingOut,
)
from app.services.sensor_health import compute_sensor_health

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sensors", tags=["sensors"])


def _to_sensor_out(sensor: Sensor) -> SensorOut:
    return SensorOut(
        id=sensor.id,
        name=sensor.name,
        sensor_type=sensor.sensor_type,
        lat=sensor.lat,
        lng=sensor.lng,
        district=sensor.district,
        state=sensor.state,
        is_active=sensor.is_active,
        last_seen=sensor.last_seen,
        health=compute_sensor_health(sensor.last_seen),
        data_label=sensor.data_label,
        created_at=sensor.created_at,
    )


# ─── A. Register Sensor (officer / admin only) ────────────────────────────────

@router.post("/register", response_model=SensorOut, status_code=status.HTTP_201_CREATED)
async def register_sensor(
    data: SensorRegisterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    """
    Register a known sensor station.
    Rejects duplicate sensor IDs cleanly.
    """
    existing_result = await db.execute(select(Sensor).where(Sensor.id == data.id))
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400,
            detail=f"Sensor with id '{data.id}' already exists",
        )

    sensor = Sensor(
        id=data.id,
        name=data.name,
        sensor_type=data.sensor_type,
        lat=data.lat,
        lng=data.lng,
        district=data.district,
        state=data.state,
        is_active=data.is_active,
        data_label=data.data_label,
        created_at=datetime.utcnow(),
    )
    db.add(sensor)
    await db.flush()
    await db.refresh(sensor)

    logger.info("[SENSOR] Registered sensor %s (%s) by user %s", sensor.id, sensor.name, current_user.id)
    return _to_sensor_out(sensor)


# ─── B. Ingest Telemetry ──────────────────────────────────────────────────────

@router.post("/ingest", response_model=SensorReadingOut, status_code=status.HTTP_201_CREATED)
async def ingest_telemetry(
    data: SensorReadingCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Receive telemetry from a registered sensor.
    - Validates payload
    - Verifies sensor existence and active state
    - Persists observation
    - Updates sensor.last_seen
    - Handles duplicates idempotently (HTTP 200)
    """
    sensor_result = await db.execute(select(Sensor).where(Sensor.id == data.sensor_id))
    sensor = sensor_result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{data.sensor_id}' not found")

    if not sensor.is_active:
        raise HTTPException(status_code=400, detail=f"Sensor '{data.sensor_id}' is inactive")

    # Check for existing duplicate reading for fast-path idempotency
    dup_result = await db.execute(
        select(SensorReading).where(
            SensorReading.sensor_id == data.sensor_id,
            SensorReading.timestamp == data.timestamp,
        )
    )
    existing_reading = dup_result.scalar_one_or_none()
    if existing_reading:
        # Idempotent response: update last_seen and return existing reading with 200 OK
        response.status_code = status.HTTP_200_OK
        sensor.last_seen = datetime.utcnow()
        await db.flush()
        return existing_reading

    reading = SensorReading(
        sensor_id=data.sensor_id,
        timestamp=data.timestamp,
        rainfall_mm=data.rainfall_mm,
        soil_moisture_pct=data.soil_moisture_pct,
        tilt_degrees=data.tilt_degrees,
        temperature_c=data.temperature_c,
        battery_pct=data.battery_pct,
        data_label=data.data_label,
        created_at=datetime.utcnow(),
    )
    db.add(reading)
    # Telemetry updates sensor liveness
    sensor.last_seen = datetime.utcnow()

    try:
        await db.flush()
        await db.refresh(reading)
    except IntegrityError:
        # Concurrent duplicate collision on uix_sensor_reading_time
        await db.rollback()
        retry_result = await db.execute(
            select(SensorReading).where(
                SensorReading.sensor_id == data.sensor_id,
                SensorReading.timestamp == data.timestamp,
            )
        )
        existing = retry_result.scalar_one_or_none()
        if existing:
            response.status_code = status.HTTP_200_OK
            return existing
        raise HTTPException(status_code=400, detail="Duplicate sensor observation rejected")

    return reading


# ─── C. Sensor Heartbeat ──────────────────────────────────────────────────────

@router.post("/{sensor_id}/heartbeat", response_model=SensorOut)
async def sensor_heartbeat(
    sensor_id: str,
    data: Optional[SensorHeartbeat] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lightweight liveness heartbeat for a sensor.
    Updates last_seen and returns updated health.
    """
    sensor_result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    sensor = sensor_result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")

    if not sensor.is_active:
        raise HTTPException(status_code=400, detail=f"Sensor '{sensor_id}' is inactive")

    sensor.last_seen = datetime.utcnow()
    await db.flush()
    await db.refresh(sensor)

    return _to_sensor_out(sensor)


# ─── D. List Sensors ──────────────────────────────────────────────────────────

@router.get("", response_model=list[SensorOut])
async def list_sensors(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by health: ONLINE, STALE, OFFLINE"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all registered sensors with computed health status.
    """
    result = await db.execute(select(Sensor).order_by(Sensor.created_at.desc()))
    sensors = result.scalars().all()

    sensor_outs = [_to_sensor_out(s) for s in sensors]
    if status_filter:
        target = status_filter.upper()
        sensor_outs = [s for s in sensor_outs if s.health == target]

    return sensor_outs


# ─── E. Get Sensor Readings (Bounded History) ─────────────────────────────────

@router.get("/{sensor_id}/readings", response_model=list[SensorReadingOut])
async def get_sensor_readings(
    sensor_id: str,
    limit: int = Query(50, ge=1, le=500, description="Max readings to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return recent observation history for a specific sensor.
    Bounded query by limit (default 50, max 500).
    """
    sensor_result = await db.execute(select(Sensor).where(Sensor.id == sensor_id))
    sensor = sensor_result.scalar_one_or_none()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")

    readings_result = await db.execute(
        select(SensorReading)
        .where(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
    )
    readings = readings_result.scalars().all()
    return readings
