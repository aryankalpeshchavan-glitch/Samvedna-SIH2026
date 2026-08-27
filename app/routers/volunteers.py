from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import require_role
from app.models.volunteer import Volunteer
from app.models.user import User
from app.schemas.volunteer import VolunteerHeartbeat, VolunteerOut

router = APIRouter(prefix="/volunteers", tags=["volunteers"])


def skills_to_str(skills: list[str]) -> str:
    return ",".join(skills) if skills else ""


@router.post("/heartbeat", response_model=VolunteerOut)
async def heartbeat(
    data: VolunteerHeartbeat,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("volunteer", "officer", "admin")),
):
    result = await db.execute(select(Volunteer).where(Volunteer.user_id == current_user.id))
    vol = result.scalar_one_or_none()

    if vol:
        vol.lat = data.lat
        vol.lng = data.lng
        vol.availability_status = data.availability_status.value
        vol.skills = skills_to_str(data.skills)
        vol.last_heartbeat = datetime.utcnow()
    else:
        vol = Volunteer(
            user_id=current_user.id,
            skills=skills_to_str(data.skills),
            lat=data.lat,
            lng=data.lng,
            availability_status=data.availability_status.value,
            last_heartbeat=datetime.utcnow(),
        )
        db.add(vol)

    await db.flush()
    await db.refresh(vol)
    return vol
