from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import require_role, get_current_user
from app.models.audit import AuditLog
from app.models.user import User

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[dict])
async def query_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity_type: Incident, Assignment, Resource"),
    entity_id: Optional[str] = Query(None, description="Filter by entity_id"),
    action: Optional[str] = Query(None, description="Filter by action: create, verify, assign, etc."),
    incident_id: Optional[str] = Query(None, description="Alias for entity_id when entity_type=Incident"),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    """
    Queryable audit log for security/audit requirement (F10).
    Returns audit entries with incident_id, event_type, actor, timestamp, previous_state, new_state.
    """
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    # incident_id is convenience alias
    effective_id = incident_id or entity_id
    if effective_id:
        query = query.where(AuditLog.entity_id == effective_id)
    if action:
        query = query.where(AuditLog.action == action)

    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "actor_id": log.actor_id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "incident_id": log.entity_id if log.entity_type == "Incident" else None,
            "event_type": log.action,
            "actor": log.actor_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "previous_state": log.before,
            "new_state": log.after,
            "before": log.before,
            "after": log.after,
        }
        for log in logs
    ]
