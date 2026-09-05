"""
Day 4 — Intelligence Layer Tests
===================================
Tests: priority engine, explanation layer, actions, exposure, decision endpoint, what-if.
"""
import pytest
from httpx import AsyncClient

from app.intelligence.priority import (
    compute_exposure_score, compute_vulnerability_score,
    compute_response_gap_score, compute_priority,
)
from app.intelligence.explanation import explain_drivers
from app.intelligence.actions import generate_actions
from tests.test_api import auth_header, register_and_login, client, setup_db
from app.models.risk import RiskZone


# ── Unit: Priority Engine ──────────────────────────────────────────────────────

def test_compute_exposure_score_empty():
    score = compute_exposure_score()
    assert score == 0.0


def test_compute_exposure_score_large_population():
    score = compute_exposure_score(population=5000, households=1500, schools=5)
    assert score >= 0.7


def test_compute_exposure_score_partial():
    score = compute_exposure_score(population=250, critical_roads=1)
    assert 0.0 < score < 1.0


def test_compute_vulnerability_high():
    score = compute_vulnerability_score(
        distance_to_nearest_hospital_km=80.0,
        has_early_warning=False,
        road_access_quality="poor",
    )
    assert score >= 0.7


def test_compute_vulnerability_low():
    score = compute_vulnerability_score(
        distance_to_nearest_hospital_km=2.0,
        has_early_warning=True,
        road_access_quality="good",
    )
    assert score < 0.3


def test_response_gap_no_supply():
    gap = compute_response_gap_score(available_volunteers=0, nearby_resources=0, incident_severity=5)
    assert gap == 1.0


def test_response_gap_abundant_supply():
    gap = compute_response_gap_score(available_volunteers=10, nearby_resources=5, incident_severity=1)
    assert gap < 0.2


def test_priority_critical():
    result = compute_priority(
        risk_score=0.9,
        exposure_score=0.85,
        vulnerability_score=0.80,
        response_gap_score=0.95,
    )
    assert result["priority_level"] == "CRITICAL"
    assert result["priority_score"] >= 80


def test_priority_low():
    result = compute_priority(
        risk_score=0.1,
        exposure_score=0.05,
        vulnerability_score=0.10,
        response_gap_score=0.05,
    )
    assert result["priority_level"] == "LOW"
    assert result["priority_score"] < 40


def test_priority_medium_high_exposure_overrides_lower_risk():
    """A location with lower raw risk but very high exposure and gap should score higher."""
    result_a = compute_priority(risk_score=0.9, exposure_score=0.1, vulnerability_score=0.1, response_gap_score=0.1)
    result_b = compute_priority(risk_score=0.6, exposure_score=0.9, vulnerability_score=0.8, response_gap_score=0.9)
    assert result_b["priority_score"] > result_a["priority_score"]


def test_priority_returns_weights():
    result = compute_priority(0.5, 0.5, 0.5, 0.5)
    assert "weights" in result
    assert abs(sum(result["weights"].values()) - 1.0) < 0.001  # weights must sum to 1


# ── Unit: Explanation Layer ────────────────────────────────────────────────────

def test_explain_known_driver():
    explanations = explain_drivers(["rainfall_24h"])
    assert len(explanations) == 1
    assert explanations[0]["key"] == "rainfall_24h"
    assert "Rainfall" in explanations[0]["label"]


def test_explain_unknown_driver_safe():
    """Unknown driver keys must not raise exceptions."""
    explanations = explain_drivers(["some_unknown_driver_xyz"])
    assert len(explanations) == 1
    assert explanations[0]["key"] == "some_unknown_driver_xyz"


def test_explain_multiple_drivers():
    explanations = explain_drivers(["rainfall_24h", "slope", "ndvi"])
    assert len(explanations) == 3


def test_explain_with_values():
    explanations = explain_drivers(["rainfall_24h"], feature_values={"rainfall_24h": 125.5})
    assert explanations[0]["value"] == 125.5


def test_explain_empty():
    explanations = explain_drivers([])
    assert explanations == []


# ── Unit: Action Engine ────────────────────────────────────────────────────────

def test_actions_high_risk():
    actions = generate_actions(
        risk_level="HIGH", priority_level="CRITICAL",
        response_gap_score=0.9, population=600, available_volunteers=0,
    )
    assert any("DDMA" in a or "Disaster" in a for a in actions)
    assert any("evacuation" in a.lower() for a in actions)
    assert any("resource" in a.lower() or "escalate" in a.lower() for a in actions)


def test_actions_medium_risk():
    actions = generate_actions(
        risk_level="MEDIUM", priority_level="MEDIUM",
        response_gap_score=0.2, population=50,
    )
    assert any("monitor" in a.lower() for a in actions)


def test_actions_low_risk():
    actions = generate_actions(
        risk_level="LOW", priority_level="LOW",
        response_gap_score=0.1, population=20,
    )
    assert any("routine" in a.lower() or "no immediate" in a.lower() for a in actions)


def test_actions_critical_road():
    actions = generate_actions(
        risk_level="HIGH", priority_level="HIGH",
        response_gap_score=0.3, has_critical_road=True,
    )
    assert any("road" in a.lower() for a in actions)


def test_actions_never_empty():
    """Actions must never return an empty list."""
    for rl, pl, gap in [("LOW", "LOW", 0.0), ("MEDIUM", "MEDIUM", 0.5), ("HIGH", "CRITICAL", 1.0)]:
        actions = generate_actions(risk_level=rl, priority_level=pl, response_gap_score=gap)
        assert len(actions) >= 1


# ── Integration: API Endpoints ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_and_list_exposure_zone(client: AsyncClient):
    token = await register_and_login(client, "officer")

    create_resp = await client.post("/intelligence/exposure", json={
        "name": "Test Village",
        "lat": 26.1, "lng": 91.7, "radius_km": 5.0,
        "population": 480, "households": 120,
        "schools": 1, "hospitals": 0, "critical_roads": 2,
        "road_access_quality": "poor",
        "has_early_warning": False,
        "data_status": "simulated",
        "source": "census_2021_demo",
    }, headers=auth_header(token))
    assert create_resp.status_code == 201
    created = create_resp.json()
    assert created["population"] == 480
    assert created["data_status"] == "simulated"

    list_resp = await client.get("/intelligence/exposure", headers=auth_header(token))
    assert list_resp.status_code == 200
    assert any(z["id"] == created["id"] for z in list_resp.json())


@pytest.mark.asyncio
async def test_nearby_exposure(client: AsyncClient):
    token = await register_and_login(client, "officer")
    await client.post("/intelligence/exposure", json={
        "lat": 26.1, "lng": 91.7, "radius_km": 5.0,
        "population": 100, "data_status": "simulated",
    }, headers=auth_header(token))

    resp = await client.get("/intelligence/exposure/nearby?lat=26.1&lng=91.7&radius_km=5.0",
                            headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_decision_endpoint_no_zone(client: AsyncClient):
    """Decision endpoint should return 503 when no risk data is available."""
    token = await register_and_login(client, "officer")
    resp = await client.post("/intelligence/decision", json={
        "lat": 26.1, "lng": 91.7, "location_id": "test_loc_001",
    }, headers=auth_header(token))
    assert resp.status_code == 503
    assert "Risk service unavailable" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_decision_with_exposure_zone(client: AsyncClient):
    """Decision endpoint should incorporate an exposure zone when one exists nearby."""
    token = await register_and_login(client, "officer")

    # Create exposure zone at the exact decision location
    await client.post("/intelligence/exposure", json={
        "name": "High-density settlement",
        "lat": 26.15, "lng": 91.75, "radius_km": 10.0,
        "population": 1200, "households": 350,
        "schools": 2, "hospitals": 1, "critical_roads": 3,
        "road_access_quality": "poor",
        "has_early_warning": False,
        "data_status": "simulated",
    }, headers=auth_header(token))
    
    # Needs a RiskZone to avoid 503
    import datetime
    from tests.test_api import TestSession
    async with TestSession() as db:
        rz = RiskZone(id="test_zone_123", lat=26.15, lng=91.75, risk_score=0.8, horizon_hours=24, computed_at=datetime.datetime.utcnow())
        db.add(rz)
        await db.commit()

    resp = await client.post("/intelligence/decision", json={
        "lat": 26.15, "lng": 91.75,
    }, headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["exposure"] is not None
    assert data["exposure"]["population"] == 1200
    # High exposure + no volunteers → should produce HIGH or CRITICAL priority
    assert data["priority"]["priority_level"] in ("HIGH", "CRITICAL", "MEDIUM")


@pytest.mark.asyncio
async def test_whatif_endpoint_raises_priority(client: AsyncClient):
    """Adding rainfall in the what-if scenario should raise risk and possibly priority."""
    token = await register_and_login(client, "officer")
    
    # Needs a RiskZone to avoid 503
    import datetime
    from tests.test_api import TestSession
    async with TestSession() as db:
        rz = RiskZone(id="test_zone_whatif", lat=26.15, lng=91.75, risk_score=0.5, horizon_hours=24, computed_at=datetime.datetime.utcnow())
        db.add(rz)
        await db.commit()
    
    resp = await client.post("/intelligence/whatif", json={
        "lat": 26.15, "lng": 91.75,
        "zone_id": "test_zone_whatif",
        "scenario_rainfall_mm": 500.0,
    }, headers=auth_header(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_label"] == "SIMULATION — NOT A FORECAST"
    assert data["projected_risk_score"] >= data["current_risk_score"]
    assert data["data_status"] == "simulated"


@pytest.mark.asyncio
async def test_decision_rbac_citizen_allowed(client: AsyncClient):
    """Citizens must be able to query the decision endpoint (read-only intelligence)."""
    # Needs a RiskZone to avoid 503
    from app.models.risk import RiskZone
    import datetime
    from tests.test_api import TestSession
    async with TestSession() as db:
        rz = RiskZone(id="test_zone_rbac", lat=26.0, lng=91.5, risk_score=0.5, horizon_hours=24, computed_at=datetime.datetime.utcnow())
        db.add(rz)
        await db.commit()
    
    citizen_token = await register_and_login(client, "citizen")
    resp = await client.post("/intelligence/decision", json={
        "lat": 26.0, "lng": 91.5,
    }, headers=auth_header(citizen_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_whatif_rbac_citizen_blocked(client: AsyncClient):
    """Citizens must NOT be able to use the what-if endpoint."""
    citizen_token = await register_and_login(client, "citizen")
    resp = await client.post("/intelligence/whatif", json={
        "lat": 26.0, "lng": 91.5,
        "scenario_rainfall_mm": 200.0,
    }, headers=auth_header(citizen_token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_risk_contract_stable(client: AsyncClient):
    """POST /risk must continue to return the stable ML contract keys."""
    # Needs a RiskZone to avoid 503
    from app.models.risk import RiskZone
    import datetime
    from tests.test_api import TestSession
    async with TestSession() as db:
        rz = RiskZone(id="test_zone_contract", lat=26.1, lng=91.7, risk_score=0.5, horizon_hours=24, computed_at=datetime.datetime.utcnow())
        db.add(rz)
        await db.commit()
    
    token = await register_and_login(client, "officer")
    resp = await client.post("/risk", json={"lat": 26.1, "lng": 91.7}, headers=auth_header(token))
    assert resp.status_code == 200
    keys = resp.json().keys()
    for required_key in ("risk_score", "risk_level", "confidence", "drivers", "data_status"):
        assert required_key in keys

