from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ResourceType(str, Enum):
    boat = "boat"
    generator = "generator"
    medical = "medical"
    shelter = "shelter"
    vehicle = "vehicle"


class ResourceStatus(str, Enum):
    available = "available"
    committed = "committed"


class ResourceCreate(BaseModel):
    type: ResourceType
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    status: ResourceStatus = ResourceStatus.available
    data_label: str = Field(default="synthetic", pattern=r"^(live|synthetic|replayed)$")


class ResourceOut(BaseModel):
    id: str
    owner_id: int
    type: ResourceType
    lat: float
    lng: float
    status: ResourceStatus
    data_label: str
    created_at: datetime

    model_config = {"from_attributes": True}
