from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.models.user import User

router = APIRouter(tags=["status"])


@router.get("/status/{incident_id}")
async def get_incident_status(
    incident_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    incident_result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = incident_result.scalar_one_or_none()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    assignment_result = await db.execute(
        select(Assignment).where(Assignment.incident_id == incident_id)
        .order_by(Assignment.assigned_at.desc()).limit(1)
    )
    assignment = assignment_result.scalar_one_or_none()

    return {
        "incident_id": str(incident.id),
        "status": incident.status,
        "severity": incident.severity,
        "assignment": {
            "id": str(assignment.id),
            "volunteer_id": assignment.volunteer_id,
            "status": assignment.status,
            "sla_deadline": assignment.sla_deadline.isoformat(),
        } if assignment else None,
        "updated_at": incident.updated_at.isoformat(),
    }
