import asyncio
from datetime import datetime

from sqlalchemy import select

from app.core.database import async_session
from app.models.assignment import Assignment
from app.models.incident import Incident
from app.notifications.dispatcher import on_assignment_reassigned
from app.matching.engine import find_best_volunteer


async def auto_reassign_loop(interval_seconds: int = 60):
    while True:
        try:
            await check_and_reassign_expired()
        except Exception as e:
            print(f"[AUTO_REASSIGN ERROR] {e}")
        await asyncio.sleep(interval_seconds)


async def check_and_reassign_expired():
    async with async_session() as db:
        now = datetime.utcnow()
        result = await db.execute(
            select(Assignment).where(
                Assignment.status == "pending",
                Assignment.sla_deadline < now,
            )
        )
        expired = result.scalars().all()

        for assignment in expired:
            assignment.status = "reassigned"

            incident_result = await db.execute(
                select(Incident).where(Incident.id == assignment.incident_id)
            )
            incident = incident_result.scalar_one_or_none()
            if not incident:
                continue

            best = await find_best_volunteer(db, incident)
            if best:
                new_volunteer, score = best
                from datetime import timedelta
                new_assignment = Assignment(
                    incident_id=incident.id,
                    volunteer_id=new_volunteer.id,
                    sla_deadline=now + timedelta(minutes=5),
                )
                db.add(new_assignment)
                incident.status = "assigned"
                incident.updated_at = now

                await on_assignment_reassigned(
                    incident_id=str(incident.id),
                    volunteer_id=new_volunteer.id,
                    data_label=incident.data_label,
                )

                print(
                    f"[AUTO_REASSIGN] Reassigned incident {incident.id} "
                    f"from volunteer {assignment.volunteer_id} to {new_volunteer.id} "
                    f"(score={score})"
                )

        await db.commit()
