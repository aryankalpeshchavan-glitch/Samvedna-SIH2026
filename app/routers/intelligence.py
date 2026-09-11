"""
Day 4 — Intelligence / Decision Layer Router
=============================================
Connects: Risk → Explanation → Exposure → Priority → Actions

Endpoints:
  POST /intelligence/decision          — combined decision view
  GET  /intelligence/decision/{zone_id} — decision for a known risk zone
  POST /intelligence/whatif            — scenario simulator (labelled as SIMULATION)
  GET  /intelligence/exposure          — list exposure zones
  POST /intelligence/exposure          — create exposure zone
  GET  /intelligence/exposure/nearby   — nearby exposure zones
"""
import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.risk import RiskZone
from app.models.exposure import ExposureZone
from app.models.volunteer import Volunteer
from app.models.resource import Resource
from app.models.user import User
from app.models.incident import Incident
from app.schemas.intelligence import (
    DecisionRequest, DecisionResponse,
    ExposureCreate, ExposureOut,
    WhatIfRequest, WhatIfResponse,
    DriverExplanation, ExposureSummary, PriorityResult, RiskSummary,
)
from app.core.config import settings
from app.intelligence.explanation import explain_drivers, get_model_attributions
from app.intelligence.priority import (
    compute_exposure_score, compute_vulnerability_score,
    compute_response_gap_score, compute_priority,
)
from app.intelligence.actions import generate_actions
from app.services.prediction_service import prediction_service
from app.intelligence.rag_service import rag_gemini_service

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _risk_level(score: float) -> str:
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


# ─── Shared decision computation helper ───────────────────────────────────────
async def _build_decision(
    lat: float,
    lng: float,
    db: AsyncSession,
    zone: Optional[RiskZone] = None,
    location_id: Optional[str] = None,
    risk_override: Optional[float] = None,
) -> DecisionResponse:
    now = datetime.now(timezone.utc)

    # 1. Risk data — try live prediction if no zone provided
    if zone:
        risk_score = risk_override if risk_override is not None else zone.risk_score
        raw_features = zone.top_features or {}
        drivers = list(raw_features.keys())[:5] if raw_features else [
            "rainfall_24h", "rainfall_7day", "rainfall_3day"
        ]
        data_status = zone.data_label
        zone_id_str = zone.id
        confidence = zone.confidence or 0.5
        model_version = zone.model_version
        
        # Check freshness
        if zone.computed_at and (now - zone.computed_at.replace(tzinfo=timezone.utc)).total_seconds() > settings.RISK_FRESHNESS_MINUTES * 60:
            data_status = "stale"
            
    elif risk_override is not None:
        # What-if scenario override
        risk_score = risk_override
        raw_features = {}
        drivers = ["rainfall_24h", "rainfall_7day", "rainfall_3day"]
        data_status = "simulated"
        zone_id_str = location_id or "unknown"
        confidence = 0.60
        model_version = None
    else:
        # No zone and no override — try live prediction service
        if prediction_service.is_available:
            live_result = prediction_service.predict_hazard(lat=lat, lng=lng)
            if live_result is not None:
                risk_score = live_result.risk_score
                raw_features = live_result.feature_importances
                drivers = live_result.top_drivers
                data_status = "live"
                zone_id_str = location_id or f"live-{lat}-{lng}"
                confidence = live_result.confidence
                model_version = live_result.model_version
            else:
                raise HTTPException(status_code=503, detail="Risk service unavailable: prediction failed", headers={"X-Error-Code": "RISK_SERVICE_UNAVAILABLE"})
        else:
            raise HTTPException(status_code=503, detail="Risk service unavailable: no risk data found for this location", headers={"X-Error-Code": "RISK_SERVICE_UNAVAILABLE"})

    risk_lv = _risk_level(risk_score)

    # 2. Explanation — use actual model attributions when available
    attributions = get_model_attributions(raw_features if raw_features else None)
    explanations = explain_drivers(drivers, raw_features if raw_features else None, attributions)
    explanation_out = [DriverExplanation(**e) for e in explanations]

    # 3. Nearest exposure zone
    exp_result = await db.execute(select(ExposureZone))
    all_exp = exp_result.scalars().all()
    nearest_exp: Optional[ExposureZone] = None
    nearest_dist = float("inf")
    for ez in all_exp:
        d = haversine_km(lat, lng, ez.lat, ez.lng)
        if d <= ez.radius_km and d < nearest_dist:
            nearest_dist = d
            nearest_exp = ez

    if nearest_exp:
        exposure_score = compute_exposure_score(
            population=nearest_exp.population,
            households=nearest_exp.households,
            schools=nearest_exp.schools,
            hospitals=nearest_exp.hospitals,
            critical_roads=nearest_exp.critical_roads,
        )
        vuln_score = compute_vulnerability_score(
            distance_to_nearest_hospital_km=nearest_exp.distance_to_hospital_km,
            has_early_warning=nearest_exp.has_early_warning,
            road_access_quality=nearest_exp.road_access_quality,
        )
        exposure_out = ExposureSummary(
            population=nearest_exp.population,
            households=nearest_exp.households,
            schools=nearest_exp.schools,
            hospitals=nearest_exp.hospitals,
            critical_roads=nearest_exp.critical_roads,
            data_status=nearest_exp.data_status,
            source=nearest_exp.source,
        )
    else:
        # No exposure zone registered — use conservative defaults
        exposure_score = 0.30
        vuln_score = 0.50
        exposure_out = None

    # 4. Response availability
    vol_result = await db.execute(
        select(Volunteer).where(Volunteer.availability_status == "available")
    )
    available_volunteers = [
        v for v in vol_result.scalars().all()
        if haversine_km(lat, lng, v.lat, v.lng) <= 25.0
    ]
    n_volunteers = len(available_volunteers)

    res_result = await db.execute(
        select(Resource).where(Resource.status == "available")
    )
    nearby_resources = [
        r for r in res_result.scalars().all()
        if haversine_km(lat, lng, r.lat, r.lng) <= 10.0
    ]
    n_resources = len(nearby_resources)

    response_gap = compute_response_gap_score(
        available_volunteers=n_volunteers,
        nearby_resources=n_resources,
        incident_severity=5 if risk_lv == "HIGH" else 3 if risk_lv == "MEDIUM" else 1,
    )

    # 5. Priority
    priority = compute_priority(
        risk_score=risk_score,
        exposure_score=exposure_score,
        vulnerability_score=vuln_score,
        response_gap_score=response_gap,
    )
    priority_out = PriorityResult(**priority)

    # 6. Actions
    actions = generate_actions(
        risk_level=risk_lv,
        priority_level=priority["priority_level"],
        response_gap_score=response_gap,
        has_critical_road=nearest_exp.critical_roads > 0 if nearest_exp else False,
        has_hospital=nearest_exp.hospitals > 0 if nearest_exp else False,
        has_school=nearest_exp.schools > 0 if nearest_exp else False,
        population=nearest_exp.population if nearest_exp else 0,
        available_volunteers=n_volunteers,
    )

    # 7. Grounded RAG & Gemini Operational Synthesis
    inc_result = await db.execute(
        select(Incident).where(Incident.status.in_(["verified", "investigating", "reported"]))
    )
    nearby_incidents = [
        f"{i.type} ({i.status})"
        for i in inc_result.scalars().all()
        if haversine_km(lat, lng, i.lat, i.lng) <= 25.0
    ]

    ai_res = rag_gemini_service.generate_explanation(
        risk_score=risk_score,
        risk_level=risk_lv,
        confidence=confidence,
        model_version=model_version,
        top_drivers=drivers,
        driver_attributions=attributions or {},
        environmental_inputs=raw_features if raw_features else None,
        exposure=exposure_out.model_dump() if exposure_out else None,
        priority_score=priority_out.priority_score,
        priority_level=priority_out.priority_level,
        response_gap_score=response_gap,
        available_volunteers=n_volunteers,
        nearby_resources=n_resources,
        verified_incidents=nearby_incidents,
    )

    return DecisionResponse(
        location_id=zone_id_str,
        lat=lat,
        lng=lng,
        risk=RiskSummary(
            risk_score=round(risk_score, 4),
            risk_level=risk_lv,
            confidence=confidence,
            drivers=drivers,
            data_status=data_status,
        ),
        explanation=explanation_out,
        exposure=exposure_out,
        priority=priority_out,
        actions=actions,
        data_status=data_status,
        computed_at=now,
        ai_summary=ai_res.summary,
        ai_driver_analysis=ai_res.driver_analysis,
        ai_vulnerability_impact=ai_res.vulnerability_impact,
        sop_citations=ai_res.citations,
        ai_provider=ai_res.ai_provider,
    )


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/decision", response_model=DecisionResponse)
async def decision_by_location(
    data: DecisionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Main Day 4 intelligence endpoint.
    Computes Risk → Explanation → Exposure → Priority → Actions for a lat/lng.
    """
    zone = None

    if data.zone_id:
        zone_result = await db.execute(
            select(RiskZone).where(RiskZone.id == data.zone_id)
        )
        zone = zone_result.scalar_one_or_none()
    else:
        all_zones_result = await db.execute(
            select(RiskZone)
            .order_by(RiskZone.computed_at.desc())
            .limit(50)
        )
        all_zones = all_zones_result.scalars().all()

        nearest, nearest_d = None, float("inf")
        for z in all_zones:
            if z.lat and z.lng:
                d = haversine_km(data.lat, data.lng, z.lat, z.lng)
                if d < nearest_d:
                    nearest_d = d
                    nearest = z
        zone = nearest

    try:
        return await _build_decision(
            lat=data.lat,
            lng=data.lng,
            db=db,
            zone=zone,
            location_id=data.location_id,
        )

    except HTTPException:
        # Preserve the original FastAPI error (503, 404, etc.)
        raise

    except Exception as e:
        logger.exception("Decision endpoint failed")
        raise HTTPException(
            status_code=503,
            detail=f"Risk service unavailable: {str(e)}"
        )


@router.get("/decision/{zone_id}", response_model=DecisionResponse)
async def decision_by_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Decision view for a specific stored RiskZone."""
    zone_result = await db.execute(select(RiskZone).where(RiskZone.id == zone_id))
    zone = zone_result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Risk zone not found")
    if zone.lat is None or zone.lng is None:
        raise HTTPException(status_code=400, detail="Risk zone has no location data")

    return await _build_decision(
        lat=zone.lat,
        lng=zone.lng,
        db=db,
        zone=zone,
        location_id=zone_id,
    )


@router.post("/whatif", response_model=WhatIfResponse)
async def what_if_simulator(
    data: WhatIfRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    """
    Scenario simulator — clearly labelled as SIMULATION, not a real forecast.
    Models how additional rainfall would shift the risk and priority scores.
    """
    zone = None
    if data.zone_id:
        zone_result = await db.execute(select(RiskZone).where(RiskZone.id == data.zone_id))
        zone = zone_result.scalar_one_or_none()
    else:
        # Fall back to nearest risk zone by coordinates or latest zone
        all_zones_res = await db.execute(select(RiskZone))
        all_zones = all_zones_res.scalars().all()
        nearest_zone = None
        min_dist = float("inf")
        for z in all_zones:
            if z.lat is not None and z.lng is not None:
                d = haversine_km(data.lat, data.lng, z.lat, z.lng)
                if d < min_dist:
                    min_dist = d
                    nearest_zone = z
        if nearest_zone and min_dist <= 100.0:
            zone = nearest_zone
        elif all_zones:
            zone = sorted(all_zones, key=lambda z: z.computed_at, reverse=True)[0]

    # Current decision
    current = await _build_decision(lat=data.lat, lng=data.lng, db=db, zone=zone)

    # Scenario: extra rainfall adds a linear boost to risk score
    # 100mm additional → +0.15 risk score (conservative estimate for NER context)
    projected_risk_score = current.risk.risk_score
    if data.scenario_rainfall_mm:
        rainfall_factor = min(0.30, data.scenario_rainfall_mm / 700.0)
        projected_risk_score = min(1.0, current.risk.risk_score + rainfall_factor)

    projected = await _build_decision(
        lat=data.lat, lng=data.lng, db=db, zone=zone,
        risk_override=projected_risk_score,
    )

    return WhatIfResponse(
        scenario_label="SIMULATION — NOT A FORECAST",
        current_risk_score=round(current.risk.risk_score, 4),
        projected_risk_score=round(projected.risk.risk_score, 4),
        current_priority_level=current.priority.priority_level,
        projected_priority_level=projected.priority.priority_level,
        current_actions=current.actions,
        projected_actions=projected.actions,
        data_status="simulated",
    )


# ─── Exposure zone management ─────────────────────────────────────────────────

@router.post("/exposure", response_model=ExposureOut, status_code=201)
async def create_exposure_zone(
    data: ExposureCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("officer", "admin")),
):
    ez = ExposureZone(
        name=data.name,
        lat=data.lat,
        lng=data.lng,
        radius_km=data.radius_km,
        population=data.population,
        households=data.households,
        schools=data.schools,
        hospitals=data.hospitals,
        critical_roads=data.critical_roads,
        distance_to_hospital_km=data.distance_to_hospital_km,
        has_early_warning=data.has_early_warning,
        road_access_quality=data.road_access_quality,
        data_status=data.data_status,
        source=data.source,
        extra=data.extra or {},
    )
    db.add(ez)
    await db.flush()
    await db.refresh(ez)
    return ez


@router.get("/exposure", response_model=list[ExposureOut])
async def list_exposure_zones(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ExposureZone).order_by(ExposureZone.created_at.desc()))
    return result.scalars().all()


@router.get("/exposure/nearby", response_model=list[ExposureOut])
async def nearby_exposure_zones(
    lat: float,
    lng: float,
    radius_km: float = Query(default=10.0, ge=0.1, le=200.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(ExposureZone))
    zones = result.scalars().all()
    return [
        z for z in zones
        if haversine_km(lat, lng, z.lat, z.lng) <= radius_km
    ]
