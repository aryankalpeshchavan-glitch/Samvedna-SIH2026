from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.incident import Incident
from app.models.user import User
from app.schemas.incident import (
    IncidentCreate, IncidentOut, IncidentVerify, IncidentSMS,
    IncidentBatchSyncRequest, IncidentBatchSyncResponse,
)
from app.matching.queue import enqueue_matching_job

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

    data_label_val = data.data_label.value if data.data_label else "synthetic"
    occurred_at_val = data.occurred_at or datetime.utcnow()

    incident = Incident(
        reporter_id=current_user.id,
        type=data.type.value,
        description=data.description,
        lat=data.lat,
        lng=data.lng,
        severity=data.severity,
        photo_url=data.photo_url,
        idempotency_key=data.idempotency_key,
        data_label=data_label_val,
        occurred_at=occurred_at_val,
    )
    db.add(incident)
    try:
        await db.flush()
        await db.refresh(incident)

        # Audit + WS broadcast via same hook (single source of truth)
        try:
            from app.core.audit_logger import record_audit_log
            await record_audit_log(
                db=db,
                action="create",
                entity_type="Incident",
                entity_id=str(incident.id),
                actor_id=current_user.id,
                before=None,
                after={"status": incident.status, "type": incident.type, "data_label": data_label_val},
            )
        except Exception:
            pass

        return incident
    except IntegrityError:
        await db.rollback()
        if data.idempotency_key:
            existing = await db.execute(
                select(Incident).where(Incident.idempotency_key == data.idempotency_key)
            )
            existing_incident = existing.scalar_one_or_none()
            if existing_incident:
                return existing_incident
        raise


@router.post("/sync", response_model=IncidentBatchSyncResponse)
async def sync_incidents(
    data: IncidentBatchSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("citizen", "volunteer", "officer", "admin")),
):
    synced = []
    duplicates = []
    errors = []

    for item in data.items:
        try:
            if item.idempotency_key:
                existing_res = await db.execute(
                    select(Incident).where(Incident.idempotency_key == item.idempotency_key)
                )
                existing_incident = existing_res.scalar_one_or_none()
                if existing_incident:
                    duplicates.append(existing_incident)
                    continue

            data_label_val = item.data_label.value if item.data_label else "replayed"
            occurred_at_val = item.occurred_at or datetime.utcnow()

            incident = Incident(
                reporter_id=current_user.id,
                type=item.type.value,
                description=item.description,
                lat=item.lat,
                lng=item.lng,
                severity=item.severity,
                photo_url=item.photo_url,
                idempotency_key=item.idempotency_key,
                data_label=data_label_val,
                occurred_at=occurred_at_val,
            )
            db.add(incident)
            try:
                await db.flush()
                await db.refresh(incident)
                synced.append(incident)
            except IntegrityError:
                await db.rollback()
                if item.idempotency_key:
                    existing_res = await db.execute(
                        select(Incident).where(Incident.idempotency_key == item.idempotency_key)
                    )
                    existing_incident = existing_res.scalar_one_or_none()
                    if existing_incident:
                        duplicates.append(existing_incident)
                        continue
                raise
        except Exception as e:
            errors.append({
                "idempotency_key": item.idempotency_key,
                "error": str(e),
            })

    return IncidentBatchSyncResponse(
        synced=synced,
        duplicates=duplicates,
        errors=errors,
    )



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


VALID_INCIDENT_TRANSITIONS = {
    "reported": {"verified", "rejected", "assigned"},
    "verified": {"assigned", "rejected"},
    "assigned": {"resolved"},
    "resolved": set(),
    "rejected": set(),
}


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

    # Idempotent re-verification: no-op, no duplicate audit or matching job
    if incident.status == "verified":
        return incident

    if incident.status != "reported":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot verify incident in '{incident.status}' state",
        )

    old_status = incident.status
    incident.status = "verified"
    incident.data_label = data.data_label.value
    incident.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(incident)

    from app.core.audit_logger import record_audit_log
    await record_audit_log(
        db=db,
        action="verify",
        entity_type="Incident",
        entity_id=str(incident.id),
        actor_id=current_user.id,
        before={"status": old_status},
        after={"status": "verified", "data_label": data.data_label.value},
    )

    # Enqueue matching job for verified incident
    import asyncio
    asyncio.create_task(enqueue_matching_job(str(incident.id)))

    return incident


# ─── Alias: POST /incidents/{id}/verify ─────────────────────────────────────
# Backward-compatible alias for PATCH /incidents/{id}/verify

@router.post("/{incident_id}/verify", response_model=IncidentOut)
async def verify_incident_post_alias(
    incident_id: str,
    data: IncidentVerify,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    """
    POST alias for PATCH /incidents/{incident_id}/verify.
    Accepts the same body. Kept for frontend clients that prefer POST.
    """
    return await verify_incident(incident_id=incident_id, data=data, db=db, current_user=current_user)



@router.patch("/{incident_id}/reject", response_model=IncidentOut)
async def reject_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    if incident.status not in ["reported", "verified"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject incident in '{incident.status}' state",
        )

    old_status = incident.status
    incident.status = "rejected"
    incident.updated_at = datetime.utcnow()
    await db.flush()
    await db.refresh(incident)

    from app.core.audit_logger import record_audit_log
    await record_audit_log(
        db=db,
        action="reject",
        entity_type="Incident",
        entity_id=str(incident.id),
        actor_id=current_user.id,
        before={"status": old_status},
        after={"status": "rejected"},
    )

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
