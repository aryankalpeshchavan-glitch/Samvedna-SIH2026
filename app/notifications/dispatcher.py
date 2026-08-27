import json
from typing import Any
from datetime import datetime

from sqlalchemy import select

from app.core.database import async_session
from app.core.redis import redis_client
from app.models.notification import NotificationLog
from app.models.user import User
from app.notifications.provider import get_provider


async def dispatch_notification(
    incident_id: str | None,
    recipient_id: int,
    channel: str,
    message: str,
    data_label: str,
    extra: dict[str, Any] | None = None,
):
    provider = get_provider()

    try:
        async with async_session() as db:
            user_result = await db.execute(
                select(User).where(User.id == recipient_id)
            )
            user = user_result.scalar_one_or_none()
            recipient_phone = user.phone if user else str(recipient_id)

            log = NotificationLog(
                incident_id=incident_id,
                recipient_id=recipient_id,
                channel=channel,
                payload={"message": message, **(extra or {})},
                data_label=data_label,
                status="queued",
            )
            db.add(log)
            await db.commit()

            success = await provider.send(
                recipient=recipient_phone,
                message=message,
                channel=channel,
                data_label=data_label,
                extra=extra,
            )

            log.status = "sent" if success else "failed"
            log.sent_at = datetime.utcnow()
            await db.commit()

            if not success:
                await redis_client.lpush(
                    "notification_queue",
                    json.dumps({
                        "notification_id": str(log.id),
                        "retry_count": 0,
                    }),
                )

    except Exception as e:
        print(f"[DISPATCHER ERROR] {e}")
        await redis_client.lpush(
            "notification_queue",
            json.dumps({
                "incident_id": incident_id,
                "recipient_id": recipient_id,
                "channel": channel,
                "message": message,
                "data_label": data_label,
                "retry_count": 0,
            }),
        )


async def on_incident_verified(incident_id: str, reporter_id: int, data_label: str):
    await dispatch_notification(
        incident_id=incident_id,
        recipient_id=reporter_id,
        channel="console",
        message=f"Incident {incident_id} has been verified by an officer.",
        data_label=data_label,
    )


async def on_assignment_created(
    incident_id: str,
    volunteer_id: int,
    data_label: str,
):
    await dispatch_notification(
        incident_id=incident_id,
        recipient_id=volunteer_id,
        channel="console",
        message=f"You have been assigned to incident {incident_id}. Please respond within 5 minutes.",
        data_label=data_label,
    )


async def on_assignment_reassigned(
    incident_id: str,
    volunteer_id: int,
    data_label: str,
):
    await dispatch_notification(
        incident_id=incident_id,
        recipient_id=volunteer_id,
        channel="console",
        message=f"You have been RE-ASSIGNED to incident {incident_id}. Previous volunteer did not respond.",
        data_label=data_label,
    )
