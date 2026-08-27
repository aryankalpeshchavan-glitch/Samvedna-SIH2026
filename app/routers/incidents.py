from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentOut, IncidentVerify, IncidentSMS

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentOut, status_code=201)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("citizen", "volunteer", "officer", "admin")),
):
    if data.idempotency_key:
        existing = await db.execute(
            select(Incident).where(Incident.idempotency_key == data.idempotency_key)
        )
        existing_incident = existing.scalar_one_or_none()
        if existing_incident:
            return existing_incident

    incident = Incident(
        reporter_id=current_user.id,
        type=data.type.value,
        description=data.description,
        lat=data.lat,
        lng=data.lng,
        severity=data.severity,
        photo_url=data.photo_url,
        idempotency_key=data.idempotency_key,
        data_label="synthetic",
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)
    return incident


@router.get("/{incident_id}", response_model=IncidentOut)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.patch("/{incident_id}/verify", response_model=IncidentOut)
async def verify_incident(
    incident_id: str,
    data: IncidentVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.status = "verified"
    incident.data_label = data.data_label.value
    incident.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(incident)
    return incident


@router.get("", response_model=list[IncidentOut])
async def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status"),
    bbox: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Incident)
    if status_filter:
        query = query.where(Incident.status == status_filter)
    if bbox:
        parts = [float(x) for x in bbox.split(",")]
        if len(parts) == 4:
            south, west, north, east = parts
            query = query.where(
                Incident.lat.between(south, north) & Incident.lng.between(west, east)
            )
    query = query.order_by(Incident.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/sms", response_model=IncidentOut, status_code=201)
async def create_incident_sms(
    data: IncidentSMS,
    db: AsyncSession = Depends(get_db),
):
    user_result = await db.execute(select(User).where(User.phone == data.phone))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Phone not registered")

    incident_type = "other"
    text_lower = data.text.lower()
    if "flood" in text_lower:
        incident_type = "flood"
    elif "landslide" in text_lower or "land slide" in text_lower:
        incident_type = "landslide"
    elif "earthquake" in text_lower or "quake" in text_lower:
        incident_type = "earthquake"
    elif "fire" in text_lower:
        incident_type = "fire"

    incident = Incident(
        reporter_id=user.id,
        type=incident_type,
        description=data.text,
        lat=data.lat or 0.0,
        lng=data.lng or 0.0,
        severity=2,
        data_label="live",
    )
    db.add(incident)
    await db.flush()
    await db.refresh(incident)
    return incident
