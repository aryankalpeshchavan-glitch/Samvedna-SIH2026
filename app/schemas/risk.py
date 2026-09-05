from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class RiskZoneOut(BaseModel):
    id: str
    risk_score: float = Field(..., ge=0, le=1)
    horizon_hours: int
    top_features: dict[str, Any] = {}
    data_label: str
    computed_at: datetime
    lat: Optional[float] = None
    lng: Optional[float] = None
    confidence: Optional[float] = None
    model_version: Optional[str] = None

    model_config = {"from_attributes": True}


class RiskExplainOut(BaseModel):
    zone_id: str
    risk_score: float
    top_features: dict[str, Any]
    explanation: str


class RiskPredictionRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    horizon_hours: Optional[int] = 24
    features: Optional[dict[str, Any]] = None


class RiskPredictionResponse(BaseModel):
    risk_score: float
    risk_level: str
    confidence: float
    drivers: list[str]
    data_status: str = "live"
    model_version: Optional[str] = None
    feature_attributions: Optional[dict[str, float]] = None
