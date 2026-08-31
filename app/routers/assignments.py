from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import require_role, get_current_user
from app.core.audit_logger import record_audit_log
from app.core.config import settings
from app.models.assignment import Assignment
from app.models.incident import Incident
from app.models.volunteer import Volunteer
from app.models.user import User
from app.schemas.assignment import AssignmentCreate, AssignmentOut, AssignmentStatusUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])


VALID_ASSIGNMENT_TRANSITIONS = {
    "pending": {"acked", "reassigned"},
    "acked": {"in_progress", "done"},
    "in_progress": {"done"},
    "done": set(),
    "reassigned": set(),
}


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

    if incident.status in ["rejected", "resolved"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot assign incident in '{incident.status}' state",
        )

    # Prevent duplicate active assignments
    active_assign_result = await db.execute(
        select(Assignment).where(
            Assignment.incident_id == str(data.incident_id),
            Assignment.status.in_(["pending", "acked", "in_progress"]),
        )
    )
    if active_assign_result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="An active assignment already exists for this incident",
        )

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


@router.get("/my", response_model=list[AssignmentOut])
async def get_my_assignments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("volunteer", "officer", "admin")),
):
    vol_result = await db.execute(select(Volunteer).where(Volunteer.user_id == current_user.id))
    vol = vol_result.scalar_one_or_none()
    if not vol:
        return []

    result = await db.execute(
        select(Assignment)
        .where(Assignment.volunteer_id == vol.id)
        .order_by(Assignment.assigned_at.desc())
    )
    return result.scalars().all()


@router.get("/{assignment_id}", response_model=AssignmentOut)
async def get_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Assignment).where(Assignment.id == assignment_id))
    assignment = result.scalar_one_or_none()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # If volunteer, can only view own assignment
    if current_user.role == "volunteer":
        vol_result = await db.execute(select(Volunteer).where(Volunteer.user_id == current_user.id))
        vol = vol_result.scalar_one_or_none()
        if not vol or assignment.volunteer_id != vol.id:
            raise HTTPException(status_code=403, detail="Forbidden: You can only view your own assignments")

    return assignment


@router.get("", response_model=list[AssignmentOut])
async def list_assignments(
    incident_id: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    query = select(Assignment)
    if incident_id:
        query = query.where(Assignment.incident_id == incident_id)
    if status_filter:
        query = query.where(Assignment.status == status_filter)
    query = query.order_by(Assignment.assigned_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.patch("/{assignment_id}/status", response_model=AssignmentOut)
@router.post("/{assignment_id}/status", response_model=AssignmentOut)
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

    # Volunteer can only modify their own assignment
    if current_user.role == "volunteer":
        vol_result = await db.execute(select(Volunteer).where(Volunteer.user_id == current_user.id))
        vol = vol_result.scalar_one_or_none()
        if not vol or assignment.volunteer_id != vol.id:
            raise HTTPException(status_code=403, detail="Forbidden: You can only update your own assignment")

    old_status = assignment.status
    target_status = data.status.value

    # Idempotent if already in target status
    if old_status == target_status:
        return assignment

    # Validate state transition
    allowed = VALID_ASSIGNMENT_TRANSITIONS.get(old_status, set())
    if target_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid state transition from '{old_status}' to '{target_status}'",
        )

    assignment.status = target_status
    if target_status == "acked":
        assignment.acked_at = datetime.utcnow()

    if target_status == "done":
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
        action=f"status_{target_status}",
        entity_type="Assignment",
        entity_id=str(assignment.id),
        actor_id=current_user.id,
        before={"status": old_status},
        after={"status": target_status},
    )

    return assignment


@router.post("/{assignment_id}/ack", response_model=AssignmentOut)
async def ack_assignment(
    assignment_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("volunteer", "officer", "admin")),
):
    """Convenience endpoint to acknowledge an assignment."""
    from app.schemas.assignment import AssignmentStatus
    return await update_assignment_status(
        assignment_id=assignment_id,
        data=AssignmentStatusUpdate(status=AssignmentStatus.acked),
        db=db,
        current_user=current_user,
    )
