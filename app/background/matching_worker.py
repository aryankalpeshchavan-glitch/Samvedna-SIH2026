import asyncio
import json
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.redis import get_redis
from app.core.database import async_session
from app.core.audit_logger import record_audit_log
from app.core.config import settings
from app.models.incident import Incident
from app.models.assignment import Assignment
from app.matching.engine import find_best_volunteer
from app.notifications.dispatcher import on_assignment_created

logger = logging.getLogger(__name__)


async def process_matching_queue():
    """
    Background worker that continuously pulls from the matching queue
    and assigns incidents to the best available volunteer.
    """
    redis = await get_redis()
    if not redis:
        logger.warning("[MATCHING_WORKER] Redis not available, shutting down worker.")
        return

    logger.info("[MATCHING_WORKER] Started listening to matching_queue...")
    while True:
        try:
            # Block until a job is available in the matching_queue (timeout 5s)
            result = await redis.brpop("matching_queue", timeout=5)
            if not result:
                continue

            queue_name, payload_bytes = result
            payload = json.loads(payload_bytes)
            incident_id = payload.get("incident_id")
            if not incident_id:
                continue

            await process_incident_match(incident_id)

        except asyncio.CancelledError:
            logger.info("[MATCHING_WORKER] Shutting down...")
            break
        except Exception as e:
            logger.error("[MATCHING_WORKER] Error processing queue: %s", e)
            await asyncio.sleep(5)


async def process_incident_match(incident_id: str):
    async with async_session() as db:
        now = datetime.utcnow()

        # 1. Fetch the incident
        result = await db.execute(select(Incident).where(Incident.id == incident_id))
        incident = result.scalar_one_or_none()

        if not incident:
            logger.warning("[MATCHING_WORKER] Incident %s not found.", incident_id)
            return

        # Only process if verified
        if incident.status != "verified":
            logger.info(
                "[MATCHING_WORKER] Incident %s is %s, skipping match.",
                incident_id, incident.status,
            )
            return

        # 2. Check if already assigned (safety check)
        existing_assignment_result = await db.execute(
            select(Assignment).where(
                Assignment.incident_id == incident_id,
                Assignment.status.in_(["pending", "acked", "in_progress", "done"])
            )
        )
        if existing_assignment_result.scalars().first():
            logger.info(
                "[MATCHING_WORKER] Incident %s already has an active assignment.", incident_id
            )
            return

        # 3. Find the best volunteer
        best = await find_best_volunteer(db, incident)
        if not best:
            logger.warning(
                "[MATCHING_WORKER] No suitable volunteers found for incident %s.", incident_id
            )
            await record_audit_log(
                db=db,
                action="matching_no_resource",
                entity_type="Incident",
                entity_id=str(incident.id),
                actor_id=None,
                before=None,
                after={"status": incident.status, "reason": "no_available_volunteers"},
            )
            await db.commit()
            return

        new_volunteer, score = best

        # 4. Create assignment
        new_assignment = Assignment(
            incident_id=incident.id,
            volunteer_id=new_volunteer.id,
            sla_deadline=now + timedelta(seconds=settings.ASSIGNMENT_ACK_TIMEOUT_SECONDS),
            status="pending"
        )
        db.add(new_assignment)

        # 5. Update incident status
        incident.status = "assigned"
        incident.updated_at = now

        try:
            await db.flush()
            await db.refresh(new_assignment)
        except IntegrityError:
            await db.rollback()
            logger.info(
                "[MATCHING_WORKER] Active assignment already exists for incident %s (collision with concurrent assignment). Skipping.",
                incident_id,
            )
            return

        # 6. Audit log for assignment creation
        await record_audit_log(
            db=db,
            action="assign",
            entity_type="Assignment",
            entity_id=str(new_assignment.id),
            actor_id=None,
            before=None,
            after={
                "status": "pending",
                "volunteer_id": new_volunteer.id,
                "incident_id": str(incident.id)
            },
        )

        # 7. Dispatch notification
        await on_assignment_created(
            incident_id=str(incident.id),
            volunteer_id=new_volunteer.id,
            data_label=incident.data_label,
        )

        await db.commit()
        logger.info(
            "[MATCHING_WORKER] Successfully matched incident %s to volunteer %s (score: %s)",
            incident_id, new_volunteer.id, score,
        )
