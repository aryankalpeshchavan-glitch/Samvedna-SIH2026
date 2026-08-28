from datetime import datetime
from uuid import uuid4

from sqlalchemy import event

from app.models.audit import AuditLog


from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession


async def record_audit_log(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: str,
    actor_id: Optional[int] = None,
    before: Optional[dict[str, Any]] = None,
    after: Optional[dict[str, Any]] = None,
) -> AuditLog:
    """
    Explicitly logs an auditable state transition into the audit_log table.
    """
    entry = AuditLog(
        id=str(uuid4()),
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        before=before,
        after=after,
        timestamp=datetime.utcnow(),
    )
    db.add(entry)
    return entry


def _model_to_dict(instance) -> dict:
    return {
        c.key: str(getattr(instance, c.key))
        for c in instance.__table__.columns
        if getattr(instance, c.key) is not None
    }


def _extract_id(instance) -> str:
    pk = instance.__table__.primary_key.columns.values()[0]
    val = getattr(instance, pk.key)
    return str(val) if val else "unknown"


def setup_audit_listeners():
    tracked = {"Incident", "Assignment", "Resource"}

    def after_insert(mapper, connection, target):
        if type(target).__name__ not in tracked:
            return
        actor_id = getattr(target, "reporter_id", None) or getattr(target, "owner_id", None) or getattr(target, "user_id", None) or None
        connection.execute(
            AuditLog.__table__.insert().values(
                id=str(uuid4()), actor_id=actor_id, action="create",
                entity_type=type(target).__name__, entity_id=_extract_id(target),
                after=_model_to_dict(target), timestamp=datetime.utcnow(),
            )
        )

    def after_update(mapper, connection, target):
        if type(target).__name__ not in tracked:
            return
        actor_id = getattr(target, "reporter_id", None) or getattr(target, "owner_id", None) or getattr(target, "user_id", None) or None
        connection.execute(
            AuditLog.__table__.insert().values(
                id=str(uuid4()), actor_id=actor_id, action="update",
                entity_type=type(target).__name__, entity_id=_extract_id(target),
                after=_model_to_dict(target), timestamp=datetime.utcnow(),
            )
        )

    from app.models.incident import Incident
    from app.models.assignment import Assignment
    from app.models.resource import Resource

    for model in (Incident, Assignment, Resource):
        event.listen(model, "after_insert", after_insert)
        event.listen(model, "after_update", after_update)
