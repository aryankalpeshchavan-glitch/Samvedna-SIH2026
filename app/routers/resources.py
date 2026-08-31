import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, require_role
from app.models.resource import Resource
from app.models.user import User
from app.schemas.resource import ResourceCreate, ResourceOut

router = APIRouter(prefix="/resources", tags=["resources"])


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


@router.post("", response_model=ResourceOut, status_code=201)
async def create_resource(
    data: ResourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("citizen", "volunteer", "officer", "admin")),
):
    resource = Resource(
        owner_id=current_user.id,
        type=data.type.value,
        lat=data.lat,
        lng=data.lng,
        status=data.status.value,
        data_label=data.data_label,
    )
    db.add(resource)
    await db.flush()
    await db.refresh(resource)
    return resource


@router.get("/nearby", response_model=list[ResourceOut])
async def get_nearby_resources(
    lat: float,
    lng: float,
    type: str = None,
    radius_km: float = 10.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Resource)
    if type:
        query = query.where(Resource.type == type)
    result = await db.execute(query)
    all_resources = result.scalars().all()
    return [
        r for r in all_resources
        if haversine_km(lat, lng, r.lat, r.lng) <= radius_km
    ]


async def get_nearby_resources_for_matching(
    db: AsyncSession,
    lat: float,
    lng: float,
    resource_type: str = None,
    radius_km: float = 5.0,
) -> list:
    query = select(Resource).where(Resource.status == "available")
    if resource_type:
        query = query.where(Resource.type == resource_type)
    result = await db.execute(query)
    all_resources = result.scalars().all()
    return [
        r for r in all_resources
        if haversine_km(lat, lng, r.lat, r.lng) <= radius_km
    ]
