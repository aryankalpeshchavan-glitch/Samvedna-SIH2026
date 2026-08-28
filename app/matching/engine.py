import math
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.volunteer import Volunteer
from app.models.incident import Incident
from app.routers.resources import get_nearby_resources_for_matching


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


def parse_skills(skills_str: str) -> list[str]:
    if not skills_str:
        return []
    return [s.strip() for s in skills_str.split(",") if s.strip()]


def skill_match_score(volunteer_skills: list[str], incident_type: str) -> float:
    skill_map = {
        "flood": ["swimming", "rescue", "boat", "first_aid", "flood"],
        "landslide": ["rescue", "digging", "first_aid", "heavy_machinery"],
        "earthquake": ["rescue", "first_aid", "structural_assessment"],
        "fire": ["firefighting", "evacuation", "first_aid"],
        "other": ["general", "first_aid"],
    }
    required = set(skill_map.get(incident_type, ["general"]))
    if not volunteer_skills:
        return 0.1
    matches = required.intersection(set(volunteer_skills))
    return len(matches) / len(required) if required else 0.1


async def score(
    db: AsyncSession,
    volunteer: Volunteer,
    incident: Incident,
) -> float:
    dist_km = haversine_km(volunteer.lat, volunteer.lng, incident.lat, incident.lng)
    proximity_score = max(0.0, 1.0 - (dist_km / 50.0))

    skills = parse_skills(volunteer.skills)
    skill_score = skill_match_score(skills, incident.type)

    base = 0.6 * proximity_score + 0.4 * skill_score

    resource_boost = 0.0
    resources = await get_nearby_resources_for_matching(
        db, incident.lat, incident.lng,
        resource_type=_incident_to_resource_type(incident.type),
        radius_km=5.0,
    )
    if resources:
        resource_boost = min(0.2, len(resources) * 0.05)

    return round(min(1.0, base + resource_boost), 4)


def _incident_to_resource_type(incident_type: str) -> Optional[str]:
    mapping = {
        "flood": "boat",
        "fire": "vehicle",
    }
    return mapping.get(incident_type)


async def find_best_volunteer(
    db: AsyncSession,
    incident: Incident,
    exclude_volunteer_ids: Optional[list[int]] = None,
) -> Optional[tuple[Volunteer, float]]:
    from sqlalchemy import select

    query = select(Volunteer).where(Volunteer.availability_status == "available")
    if exclude_volunteer_ids:
        query = query.where(~Volunteer.id.in_(exclude_volunteer_ids))
    result = await db.execute(query)
    volunteers = result.scalars().all()
    if not volunteers:
        return None

    scored = []
    for vol in volunteers:
        s = await score(db, vol, incident)
        scored.append((vol, s))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0] if scored else None
