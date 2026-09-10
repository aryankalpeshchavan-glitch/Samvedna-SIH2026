from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ─── Exposure schemas ──────────────────────────────────────────────────────────
class ExposureCreate(BaseModel):
    name: Optional[str] = None
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(default=5.0, ge=0.1, le=100.0)
    population: int = Field(default=0, ge=0)
    households: int = Field(default=0, ge=0)
    schools: int = Field(default=0, ge=0)
    hospitals: int = Field(default=0, ge=0)
    critical_roads: int = Field(default=0, ge=0)
    distance_to_hospital_km: Optional[float] = None
    has_early_warning: bool = False
    road_access_quality: str = Field(default="moderate", pattern=r"^(good|moderate|poor)$")
    data_status: str = Field(default="simulated", pattern=r"^(live|simulated|replayed|stale)$")
    source: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


class ExposureOut(BaseModel):
    id: str
    name: Optional[str] = None
    lat: float
    lng: float
    radius_km: float
    population: int
    households: int
    schools: int
    hospitals: int
    critical_roads: int
    distance_to_hospital_km: Optional[float] = None
    has_early_warning: bool
    road_access_quality: str
    data_status: str
    source: Optional[str] = None
    extra: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─── Decision schemas ─────────────────────────────────────────────────────────
class DriverExplanation(BaseModel):
    key: str
    label: str
    description: str
    unit: Optional[str] = None
    category: Optional[str] = None
    value: Optional[float] = None


class ExposureSummary(BaseModel):
    population: int
    households: int
    schools: int
    hospitals: int
    critical_roads: int
    data_status: str
    source: Optional[str] = None


class PriorityResult(BaseModel):
    priority_score: float
    priority_level: str
    weights: dict[str, float]
    factors: dict[str, float]


class RiskSummary(BaseModel):
    risk_score: float
    risk_level: str
    confidence: float
    drivers: list[str]
    data_status: str


class DecisionResponse(BaseModel):
    """
    Combined intelligence response for the Day 4 frontend decision view.
    Answers: WHY is this location important? WHAT should the authority do?
    """
    location_id: str
    lat: float
    lng: float
    risk: RiskSummary
    explanation: list[DriverExplanation]
    exposure: Optional[ExposureSummary] = None
    priority: PriorityResult
    actions: list[str]
    data_status: str
    computed_at: datetime
    ai_summary: Optional[str] = None
    ai_driver_analysis: Optional[str] = None
    ai_vulnerability_impact: Optional[str] = None
    sop_citations: Optional[list[dict[str, Any]]] = None
    ai_provider: Optional[str] = None


class DecisionRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    location_id: Optional[str] = None
    zone_id: Optional[str] = None


# ─── What-if scenario (optional P2) ──────────────────────────────────────────
class WhatIfRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    scenario_rainfall_mm: Optional[float] = Field(
        None,
        description="Scenario additional rainfall (mm) to overlay on current risk",
    )
    zone_id: Optional[str] = None


class WhatIfResponse(BaseModel):
    scenario_label: str = "SIMULATION — NOT A FORECAST"
    current_risk_score: float
    projected_risk_score: float
    current_priority_level: str
    projected_priority_level: str
    current_actions: list[str]
    projected_actions: list[str]
    data_status: str = "simulated"
