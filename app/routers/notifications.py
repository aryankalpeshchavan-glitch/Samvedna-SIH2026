from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.notification import NotificationLog
from app.models.user import User
from app.schemas.notification import NotificationLogOut

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=list[NotificationLogOut])
async def list_notifications(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("citizen", "volunteer", "officer", "admin")),
):
    query = (
        select(NotificationLog)
        .where(NotificationLog.recipient_id == current_user.id)
        .order_by(NotificationLog.sent_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
