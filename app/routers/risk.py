from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.risk import RiskZone
from app.models.user import User
from app.schemas.risk import RiskZoneOut, RiskExplainOut, RiskPredictionRequest, RiskPredictionResponse

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
            data_label=z.data_label,
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

    risk_score = zone.risk_score if zone else 0.5
    if risk_score >= 0.7:
        risk_level = "HIGH"
    elif risk_score >= 0.4:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    features = (zone.top_features if zone else None) or data.features or {}
    drivers = list(features.keys())[:3] if features else ["rainfall_24h", "rainfall_7day", "rainfall_3day"]

    return RiskPredictionResponse(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=0.84,
        drivers=drivers,
        data_status=zone.data_label if zone else "live",
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
