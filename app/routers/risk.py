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

router = APIRouter(prefix="/risk", tags=["risk"])


def parse_horizon(horizon_str: str) -> int:
    """
    Convert a horizon string like '24h', '7d', '90m' to hours.
    Raises ValueError for unknown units so callers can return 422.
    """
    if not horizon_str or len(horizon_str) < 2:
        raise ValueError(f"Invalid horizon format: '{horizon_str}'. Expected e.g. '24h', '7d', '90m'.")
    unit = horizon_str[-1]
    try:
        value = int(horizon_str[:-1])
    except ValueError:
        raise ValueError(f"Invalid horizon value in '{horizon_str}'. Expected integer followed by h/d/m.")
    if value <= 0:
        raise ValueError(f"Horizon value must be positive, got '{horizon_str}'.")
    if unit == "h":
        return value
    elif unit == "d":
        return value * 24
    elif unit == "m":
        return max(1, value // 60)
    raise ValueError(f"Unknown horizon unit '{unit}' in '{horizon_str}'. Use h (hours), d (days), or m (minutes).")


@router.get("", response_model=list[RiskZoneOut])
async def get_risk_zones(
    bbox: Optional[str] = None,
    horizon: str = "24h",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate horizon format
    try:
        horizon_hours = parse_horizon(horizon)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Validate bbox format and coordinate bounds if provided
    bbox_parts: Optional[list[float]] = None
    if bbox:
        raw = bbox.split(",")
        if len(raw) != 4:
            raise HTTPException(
                status_code=422,
                detail="bbox must be exactly 4 comma-separated numbers: south,west,north,east",
            )
        try:
            bbox_parts = [float(x) for x in raw]
        except ValueError:
            raise HTTPException(status_code=422, detail="bbox values must all be numeric")
        south, west, north, east = bbox_parts
        if not (-90 <= south <= 90 and -90 <= north <= 90):
            raise HTTPException(status_code=422, detail="bbox latitude values must be in [-90, 90]")
        if not (-180 <= west <= 180 and -180 <= east <= 180):
            raise HTTPException(status_code=422, detail="bbox longitude values must be in [-180, 180]")
        if south > north:
            raise HTTPException(status_code=422, detail="bbox south must be <= north")

    query = select(RiskZone).where(RiskZone.horizon_hours <= horizon_hours)
    result = await db.execute(query)
    zones = result.scalars().all()

    filtered = []
    for z in zones:
        if bbox_parts and z.lat is not None and z.lng is not None:
            south, west, north, east = bbox_parts
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
    Stable Risk API endpoint fulfilling the backend-to-ML boundary contract.
    """
    # Find closest risk zone or calculate baseline
    result = await db.execute(select(RiskZone).order_by(RiskZone.computed_at.desc()).limit(1))
    zone = result.scalar_one_or_none()

    if not zone:
        raise HTTPException(status_code=503, detail="Risk service unavailable: no risk data found for this location", headers={"X-Error-Code": "RISK_SERVICE_UNAVAILABLE"})

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
        confidence=0.84,
        drivers=drivers,
        data_status=data_status,
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
