from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IncidentType(str, Enum):
    landslide = "landslide"
    flood = "flood"
    earthquake = "earthquake"
    fire = "fire"
    other = "other"


class DataLabel(str, Enum):
    live = "live"
    synthetic = "synthetic"
    replayed = "replayed"


class IncidentCreate(BaseModel):
    type: IncidentType
    description: str = Field(..., max_length=2000)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    severity: int = Field(default=1, ge=1, le=5)
    photo_url: Optional[str] = None
    idempotency_key: Optional[str] = Field(default=None, max_length=128)
    occurred_at: Optional[datetime] = None
    data_label: Optional[DataLabel] = None


class IncidentOut(BaseModel):
    id: str
    reporter_id: int
    type: IncidentType
    description: str
    lat: float
    lng: float
    severity: int
    status: str
    data_label: str
    photo_url: Optional[str] = None
    occurred_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentVerify(BaseModel):
    data_label: DataLabel = DataLabel.live


class IncidentSMS(BaseModel):
    phone: str
    text: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    occurred_at: Optional[datetime] = None


class IncidentBatchSyncRequest(BaseModel):
    items: list[IncidentCreate] = Field(..., max_length=100)


class IncidentBatchSyncResponse(BaseModel):
    synced: list[IncidentOut] = Field(default_factory=list)
    duplicates: list[IncidentOut] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)

