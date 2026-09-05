from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import get_current_user
from app.models.risk import RiskZone
from app.models.user import User
from app.schemas.risk import RiskZoneOut, RiskExplainOut, RiskPredictionRequest, RiskPredictionResponse
from app.services.prediction_service import prediction_service

router = APIRouter(prefix="/risk", tags=["risk"])


def parse_horizon(horizon_str: str) -> int:
    unit = horizon_str[-1]
    value = int(horizon_str[:-1])
    if unit == "h":
        return value
    elif unit == "d":
        return value * 24
    elif unit == "m":
        return max(1, value // 60)
    return 24


@router.get("", response_model=list[RiskZoneOut])
async def get_risk_zones(
    bbox: Optional[str] = None,
    horizon: str = "24h",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    horizon_hours = parse_horizon(horizon)
    query = select(RiskZone).where(RiskZone.horizon_hours <= horizon_hours)

    result = await db.execute(query)
    zones = result.scalars().all()

    filtered = []
    for z in zones:
        if bbox and z.lat is not None and z.lng is not None:
            parts = [float(x) for x in bbox.split(",")]
            if len(parts) == 4:
                south, west, north, east = parts
                if not (south <= z.lat <= north and west <= z.lng <= east):
                    continue
        filtered.append(z)

    return [
        RiskZoneOut(
            id=z.id,
            risk_score=z.risk_score,
            horizon_hours=z.horizon_hours,
            top_features=z.top_features or {},
            data_label="stale" if (datetime.now(timezone.utc) - z.computed_at.replace(tzinfo=timezone.utc)).total_seconds() > settings.RISK_FRESHNESS_MINUTES * 60 else z.data_label,
            computed_at=z.computed_at,
            lat=z.lat,
            lng=z.lng,
            confidence=z.confidence,
            model_version=z.model_version,
        )
        for z in sorted(filtered, key=lambda z: z.risk_score, reverse=True)
    ]


@router.post("", response_model=RiskPredictionResponse)
async def predict_risk(
    data: RiskPredictionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Risk prediction endpoint.
    Calls the calibrated ML model directly via PredictionService.
    Confidence comes from the calibrated probability, not a constant.
    """
    # Try live ML inference first
    if prediction_service.is_available:
        result = prediction_service.predict(
            rainfall_24h=(data.features or {}).get("rainfall_24h", 0.0),
            rainfall_3day=(data.features or {}).get("rainfall_3day", 0.0),
            rainfall_7day=(data.features or {}).get("rainfall_7day", 0.0),
            rainfall_14day=(data.features or {}).get("rainfall_14day", 0.0),
            rainfall_30day=(data.features or {}).get("rainfall_30day", 0.0),
            elevation_m=(data.features or {}).get("elevation_m", 0.0),
            slope_deg=(data.features or {}).get("slope_deg", 0.0),
            aspect_deg=(data.features or {}).get("aspect_deg", 0.0),
            terrain_roughness=(data.features or {}).get("terrain_roughness", 0.0),
            rainfall_previous_day=(data.features or {}).get("rainfall_previous_day", 0.0),
            rainfall_2day_lag=(data.features or {}).get("rainfall_2day_lag", 0.0),
            rainfall_3day_lag=(data.features or {}).get("rainfall_3day_lag", 0.0),
            rainfall_mm=(data.features or {}).get("rainfall_mm"),
        )

        if result is not None:
            # Store prediction in RiskZone for the GET cache layer
            zone = RiskZone(
                lat=data.lat,
                lng=data.lng,
                risk_score=result.risk_score,
                horizon_hours=data.horizon_hours or 24,
                top_features=result.feature_importances,
                data_label="live",
                confidence=result.confidence,
                model_version=result.model_version,
            )
            db.add(zone)
            await db.flush()
            await db.refresh(zone)

            return RiskPredictionResponse(
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                confidence=result.confidence,
                drivers=result.top_drivers,
                data_status="live",
                model_version=result.model_version,
                feature_attributions=result.feature_importances,
            )

    # Fallback: serve from stored RiskZone cache
    result = await db.execute(select(RiskZone).order_by(RiskZone.computed_at.desc()).limit(1))
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(
            status_code=503,
            detail="Risk service unavailable: no risk data or ML model found",
            headers={"X-Error-Code": "RISK_SERVICE_UNAVAILABLE"},
        )

    risk_score = zone.risk_score
    if risk_score >= 0.7:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    features = zone.top_features or data.features or {}
    drivers = list(features.keys())[:3] if features else ["rainfall_24h", "rainfall_7day", "rainfall_3day"]

    data_status = "stale" if (datetime.now(timezone.utc) - zone.computed_at.replace(tzinfo=timezone.utc)).total_seconds() > settings.RISK_FRESHNESS_MINUTES * 60 else zone.data_label

    return RiskPredictionResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=zone.confidence or 0.5,
        drivers=drivers,
        data_status=data_status,
        model_version=zone.model_version,
        feature_attributions=features if isinstance(features, dict) else None,
    )


@router.get("/{zone_id}/explain", response_model=RiskExplainOut)
async def explain_risk_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(RiskZone).where(RiskZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Risk zone not found")

    features = zone.top_features or {}
    top_3 = sorted(features.items(), key=lambda x: abs(x[1]), reverse=True)[:3]
    explanation = "Top risk factors: " + ", ".join(
        f"{k} (impact: {v:.3f})" for k, v in top_3
    ) if top_3 else "No feature explanation available."

    return RiskExplainOut(
        zone_id=zone.id,
        risk_score=zone.risk_score,
        top_features=features,
        explanation=explanation,
    )
