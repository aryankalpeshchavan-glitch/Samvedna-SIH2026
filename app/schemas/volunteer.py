from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class AvailabilityStatus(str, Enum):
    available = "available"
    busy = "busy"
    offline = "offline"


class VolunteerHeartbeat(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    availability_status: AvailabilityStatus = AvailabilityStatus.available
    skills: list[str] = Field(default_factory=list)


class VolunteerOut(BaseModel):
    id: int
    user_id: int
    lat: float
    lng: float
    availability_status: AvailabilityStatus
    last_heartbeat: datetime
    skills: str = ""

    model_config = {"from_attributes": True}

    @property
    def skills_list(self) -> list[str]:
        if not self.skills:
            return []
        return [s.strip() for s in self.skills.split(",") if s.strip()]
