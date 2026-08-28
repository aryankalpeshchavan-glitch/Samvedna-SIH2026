from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import require_role
from app.core.audit_logger import record_audit_log
from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.volunteer import Volunteer
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentStatusUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.post("", response_model=AssignmentOut, status_code=201)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    incident_result = await db.execute(select(Incident).where(Incident.id == str(data.incident_id)))
    incident = incident_result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    vol_result = await db.execute(select(Volunteer).where(Volunteer.id == data.volunteer_id))
    vol = vol_result.scalar_one_or_none()
    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    assignment = Assignment(
        incident_id=str(data.incident_id),
        volunteer_id=data.volunteer_id,
        sla_deadline=datetime.utcnow() + timedelta(minutes=data.sla_minutes),
    )
    db.add(assignment)

    incident.status = "assigned"
    incident.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(assignment)

    await record_audit_log(
        db=db,
        action="assign",
        entity_type="Assignment",
        entity_id=str(assignment.id),
        actor_id=current_user.id,
        before=None,
        after={
            "incident_id": str(data.incident_id),
            "volunteer_id": data.volunteer_id,
            "status": "pending",
            "sla_minutes": data.sla_minutes,
        },
    )

    return assignment


@router.patch("/{assignment_id}/status", response_model=AssignmentOut)
async def update_assignment_status(
    assignment_id: str,
    data: AssignmentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("volunteer", "officer", "admin")),
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    old_status = assignment.status
    assignment.status = data.status.value
    if data.status.value == "acked":
        assignment.acked_at = datetime.utcnow()

    if data.status.value == "done":
        incident_result = await db.execute(
            select(Incident).where(Incident.id == assignment.incident_id)
        )
        incident = incident_result.scalar_one_or_none()
        if incident:
            incident.status = "resolved"
            incident.updated_at = datetime.utcnow()

    await db.flush()
    await db.refresh(assignment)

    await record_audit_log(
        db=db,
        action=f"status_{data.status.value}",
        entity_type="Assignment",
        entity_id=str(assignment.id),
        actor_id=current_user.id,
        before={"status": old_status},
        after={"status": data.status.value},
    )

    return assignment
