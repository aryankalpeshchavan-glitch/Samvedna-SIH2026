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

    model_config = {"from_attributes": True}


class RiskExplainOut(BaseModel):
    zone_id: str
    risk_score: float
    top_features: dict[str, Any]
    explanation: str
