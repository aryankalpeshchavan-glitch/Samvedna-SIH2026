from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AssignmentStatus(str, Enum):
    pending = "pending"
    acked = "acked"
    in_progress = "in_progress"
    done = "done"
    reassigned = "reassigned"


class AssignmentCreate(BaseModel):
    incident_id: UUID
    volunteer_id: int
    sla_minutes: int = Field(default=5, ge=1, le=60)


class AssignmentOut(BaseModel):
    id: UUID
    incident_id: UUID
    volunteer_id: int
    status: AssignmentStatus
    assigned_at: datetime
    acked_at: Optional[datetime] = None
    sla_deadline: datetime

    model_config = {"from_attributes": True}


class AssignmentStatusUpdate(BaseModel):
    status: AssignmentStatus
    data_label: str = Field(default="live", pattern=r"^(live|synthetic|replayed)$")
