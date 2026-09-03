import math
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from app.core.config import settings


class SensorRegisterCreate(BaseModel):
    id: str = Field(..., min_length=1, max_length=64, description="Unique sensor identifier")
    name: str = Field(..., min_length=1, max_length=100)
    sensor_type: str = Field(..., min_length=1, max_length=50)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lng: float = Field(..., ge=-180.0, le=180.0)
    district: Optional[str] = Field(None, max_length=50)
    state: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    data_label: str = Field("synthetic", max_length=20)


class SensorReadingCreate(BaseModel):
    sensor_id: str = Field(..., min_length=1, max_length=64)
    timestamp: datetime
    rainfall_mm: Optional[float] = Field(None, ge=0.0)
    soil_moisture_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    tilt_degrees: Optional[float] = Field(None, ge=0.0)
    temperature_c: Optional[float] = None
    battery_pct: Optional[float] = Field(None, ge=0.0, le=100.0)
    data_label: str = Field("synthetic", max_length=20)

    @field_validator("rainfall_mm", "soil_moisture_pct", "tilt_degrees", "temperature_c", "battery_pct", mode="before")
    @classmethod
    def validate_finite(cls, v):
        if v is not None:
            if isinstance(v, str):
                if v.strip().lower() in ("nan", "inf", "-inf", "infinity", "-infinity"):
                    raise ValueError("Numeric reading must be a finite number")
            elif isinstance(v, (int, float)):
                if math.isnan(v) or math.isinf(v):
                    raise ValueError("Numeric reading must be a finite number")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        now = datetime.utcnow()
        v_utc = v.replace(tzinfo=None) if v.tzinfo is not None else v
        if v_utc > now + timedelta(seconds=settings.SENSOR_CLOCK_SKEW_TOLERANCE_SECONDS):
            raise ValueError("Observation timestamp cannot be in the future")
        return v_utc


class SensorHeartbeat(BaseModel):
    battery_pct: Optional[float] = Field(None, ge=0.0, le=100.0)

    @field_validator("battery_pct", mode="before")
    @classmethod
    def validate_finite_battery(cls, v):
        if v is not None:
            if isinstance(v, str):
                if v.strip().lower() in ("nan", "inf", "-inf", "infinity", "-infinity"):
                    raise ValueError("Battery percentage must be a finite number")
            elif isinstance(v, (int, float)):
                if math.isnan(v) or math.isinf(v):
                    raise ValueError("Battery percentage must be a finite number")
        return v


class SensorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    sensor_type: str
    lat: float
    lng: float
    district: Optional[str] = None
    state: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    health: str = "OFFLINE"
    data_label: str
    created_at: datetime


class SensorReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sensor_id: str
    timestamp: datetime
    rainfall_mm: Optional[float] = None
    soil_moisture_pct: Optional[float] = None
    tilt_degrees: Optional[float] = None
    temperature_c: Optional[float] = None
    battery_pct: Optional[float] = None
    data_label: str
    created_at: datetime
