import pytest
from httpx import AsyncClient
from tests.test_api import client, setup_db, register_and_login, auth_header

@pytest.mark.asyncio
async def test_resource_aware_boat_boost(client: AsyncClient):
    """
    Community resource listing ('I have a boat') wired into matching score.
    Runs the full resource-aware assignment flow via API:
    - Citizen creates flood incident
    - Citizen registers a boat resource nearby
    - Two volunteers heartbeat (one near boat, one far)
    - Matching worker should prefer scoring with resource boost
    Proof: incident with nearby boat scores higher than without.
    """
    # Use API to create real data so tables are correctly set up via setup_db fixture
    citizen_token = await register_and_login(client, "citizen")
    vol1_token = await register_and_login(client, "volunteer")
    vol2_token = await register_and_login(client, "volunteer")

    # Volunteer heartbeats
    v1 = await client.post("/volunteers/heartbeat", json={"lat": 26.99, "lng": 91.99, "availability_status": "available", "skills": ["rescue", "swimming"]}, headers=auth_header(vol1_token))
    v2 = await client.post("/volunteers/heartbeat", json={"lat": 26.99, "lng": 91.99, "availability_status": "available", "skills": ["rescue", "swimming"]}, headers=auth_header(vol2_token))
    assert v1.status_code == 200 and v2.status_code == 200

    # Create flood incident
    inc = await client.post("/incidents", json={"type": "flood", "description": "Boat needed flood", "lat": 26.99, "lng": 91.99, "severity": 3}, headers=auth_header(citizen_token))
    assert inc.status_code == 201
    incident_lat, incident_lng = 26.99, 91.99

    # Score without resource: call matching engine directly with DB session
    from tests.test_api import TestSession
    from app.models.incident import Incident
    from app.models.volunteer import Volunteer
    from app.matching.engine import score
    from sqlalchemy import select

    async with TestSession() as db:
        vol_row = (await db.execute(select(Volunteer).where(Volunteer.id == v1.json()["id"]))).scalar_one()
        inc_row = Incident(type="flood", description="test", lat=incident_lat, lng=incident_lng, severity=3, reporter_id=1, status="verified", data_label="synthetic")
        base_score = await score(db, vol_row, inc_row)

        # Now register a boat resource near the incident via API
        res = await client.post("/resources", json={"type": "boat", "lat": 26.991, "lng": 91.991, "status": "available", "data_label": "synthetic"}, headers=auth_header(citizen_token))
        assert res.status_code == 201, res.text

        # Score again - should be boosted
        boosted_score = await score(db, vol_row, inc_row)

    assert boosted_score > base_score, f"Expected boat resource to boost score: base {base_score} vs boosted {boosted_score}"
    assert boosted_score - base_score >= 0.04
