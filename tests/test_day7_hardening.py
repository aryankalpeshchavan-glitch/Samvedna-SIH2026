"""
Day 7 - Production Hardening Test Suite
=========================================
Covers:
1.  POST /assignments/{id}/ack  alias endpoint
2.  POST /incidents/{id}/verify alias endpoint + RBAC
3.  CORS_ORIGINS in settings
4.  /health response includes required keys (status, version, timestamp, checks)
5.  GET /risk?bbox=  with invalid bbox (wrong count) -> 422
6.  GET /risk?bbox=  with out-of-bounds lat -> 422
7.  GET /risk?horizon= with unknown unit -> 422
8.  GET /risk?horizon= with invalid format -> 422
9.  POST /risk with out-of-bounds lat (Pydantic) -> 422
10. Dispatcher Redis resilience
11. Priority weights from settings
"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.core.config import settings
from tests.test_api import auth_header, client, register_and_login, setup_db


# --- 1. POST /assignments/{id}/ack alias ---

@pytest.mark.asyncio
async def test_ack_alias_returns_acked_status(client: AsyncClient):
    """POST /assignments/{id}/ack must transition pending->acked and return status=acked."""
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_token = await register_and_login(client, "volunteer")

    inc_resp = await client.post("/incidents", json={
        "type": "landslide", "description": "Road blocked by debris",
        "lat": 26.15, "lng": 91.75, "severity": 3,
    }, headers=auth_header(citizen_token))
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.16, "lng": 91.76, "skills": ["rescue"],
    }, headers=auth_header(vol_token))
    vol_id = vol_resp.json()["id"]

    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol_id,
    }, headers=auth_header(officer_token))
    assert assign_resp.status_code == 201
    assignment_id = assign_resp.json()["id"]

    ack_resp = await client.post(f"/assignments/{assignment_id}/ack",
                                 headers=auth_header(vol_token))
    assert ack_resp.status_code == 200, ack_resp.text
    assert ack_resp.json()["status"] == "acked"


@pytest.mark.asyncio
async def test_ack_alias_idempotent_when_already_acked(client: AsyncClient):
    """POST /ack on an already-acked assignment returns 200 without error."""
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol_token = await register_and_login(client, "volunteer")

    inc_resp = await client.post("/incidents", json={
        "type": "flood", "description": "Water rising",
        "lat": 26.10, "lng": 91.70, "severity": 2,
    }, headers=auth_header(citizen_token))
    incident_id = inc_resp.json()["id"]

    vol_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.11, "lng": 91.71, "skills": ["swimming"],
    }, headers=auth_header(vol_token))
    vol_id = vol_resp.json()["id"]

    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol_id,
    }, headers=auth_header(officer_token))
    assignment_id = assign_resp.json()["id"]

    r1 = await client.post(f"/assignments/{assignment_id}/ack", headers=auth_header(vol_token))
    assert r1.status_code == 200
    r2 = await client.post(f"/assignments/{assignment_id}/ack", headers=auth_header(vol_token))
    assert r2.status_code == 200
    assert r2.json()["status"] == "acked"


@pytest.mark.asyncio
async def test_ack_alias_wrong_volunteer_forbidden(client: AsyncClient):
    """A different volunteer cannot ACK another volunteer's assignment."""
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")
    vol1_token = await register_and_login(client, "volunteer")
    vol2_token = await register_and_login(client, "volunteer")

    inc_resp = await client.post("/incidents", json={
        "type": "fire", "description": "Forest fire",
        "lat": 26.20, "lng": 91.80, "severity": 4,
    }, headers=auth_header(citizen_token))
    incident_id = inc_resp.json()["id"]

    vol1_resp = await client.post("/volunteers/heartbeat", json={
        "lat": 26.21, "lng": 91.81, "skills": ["firefighting"],
    }, headers=auth_header(vol1_token))
    vol1_id = vol1_resp.json()["id"]

    assign_resp = await client.post("/assignments", json={
        "incident_id": incident_id, "volunteer_id": vol1_id,
    }, headers=auth_header(officer_token))
    assignment_id = assign_resp.json()["id"]

    ack_resp = await client.post(f"/assignments/{assignment_id}/ack",
                                 headers=auth_header(vol2_token))
    assert ack_resp.status_code == 403


# --- 2. POST /incidents/{id}/verify alias ---

@pytest.mark.asyncio
async def test_verify_post_alias_officer_succeeds(client: AsyncClient):
    """POST /incidents/{id}/verify must work for officers and return status=verified."""
    citizen_token = await register_and_login(client, "citizen")
    officer_token = await register_and_login(client, "officer")

    inc_resp = await client.post("/incidents", json={
        "type": "landslide", "description": "Major rockfall",
        "lat": 27.0, "lng": 92.0, "severity": 5,
    }, headers=auth_header(citizen_token))
    assert inc_resp.status_code == 201
    incident_id = inc_resp.json()["id"]

    verify_resp = await client.post(f"/incidents/{incident_id}/verify",
                                    json={"data_label": "live"},
                                    headers=auth_header(officer_token))
    assert verify_resp.status_code == 200, verify_resp.text
    assert verify_resp.json()["status"] == "verified"
    assert verify_resp.json()["data_label"] == "live"


@pytest.mark.asyncio
async def test_verify_post_alias_citizen_forbidden(client: AsyncClient):
    """Citizens must NOT be able to use POST /incidents/{id}/verify."""
    citizen_token = await register_and_login(client, "citizen")

    inc_resp = await client.post("/incidents", json={
        "type": "flood", "description": "Local flooding",
        "lat": 26.5, "lng": 91.5, "severity": 2,
    }, headers=auth_header(citizen_token))
    incident_id = inc_resp.json()["id"]

    verify_resp = await client.post(f"/incidents/{incident_id}/verify",
                                    json={"data_label": "live"},
                                    headers=auth_header(citizen_token))
    assert verify_resp.status_code == 403


@pytest.mark.asyncio
async def test_verify_post_alias_volunteer_forbidden(client: AsyncClient):
    """Volunteers must NOT be able to use POST /incidents/{id}/verify."""
    citizen_token = await register_and_login(client, "citizen")
    vol_token = await register_and_login(client, "volunteer")

    inc_resp = await client.post("/incidents", json={
        "type": "earthquake", "description": "Tremors felt",
        "lat": 26.3, "lng": 91.3, "severity": 3,
    }, headers=auth_header(citizen_token))
    incident_id = inc_resp.json()["id"]

    verify_resp = await client.post(f"/incidents/{incident_id}/verify",
                                    json={"data_label": "live"},
                                    headers=auth_header(vol_token))
    assert verify_resp.status_code == 403


# --- 3. CORS_ORIGINS setting ---

def test_cors_origins_setting_exists():
    """settings.CORS_ORIGINS must exist and return a non-empty list."""
    origins = settings.CORS_ORIGINS
    assert isinstance(origins, list), "CORS_ORIGINS must be a list"
    assert len(origins) >= 1, "CORS_ORIGINS must have at least one entry"


def test_cors_origins_default_is_wildcard():
    """Default CORS_ORIGINS contains wildcard when env var is not set."""
    import os
    original = os.environ.pop("CORS_ORIGINS", None)
    try:
        origins = settings.CORS_ORIGINS
        assert "*" in origins or origins == ["*"], \
            f"Default CORS_ORIGINS should contain '*', got {origins}"
    finally:
        if original is not None:
            os.environ["CORS_ORIGINS"] = original


def test_cors_origins_parses_json_list(monkeypatch):
    """CORS_ORIGINS env var set to JSON list is parsed correctly."""
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.com","https://app.example.com"]')
    origins = settings.CORS_ORIGINS
    assert "https://example.com" in origins
    assert "https://app.example.com" in origins


# --- 4. /health endpoint schema ---

@pytest.mark.asyncio
async def test_health_response_has_required_keys(client: AsyncClient):
    """GET /health must return status, version, timestamp, and checks."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data, "Missing key: status"
    assert "version" in data, "Missing key: version"
    assert "timestamp" in data, "Missing key: timestamp"
    assert "checks" in data, "Missing key: checks"
    assert data["status"] in ("healthy", "degraded")
    assert isinstance(data["version"], str)
    assert isinstance(data["checks"], dict)
    assert "db" in data["checks"]


# --- 5-8. Risk input validation ---

@pytest.mark.asyncio
async def test_risk_bbox_wrong_count_returns_422(client: AsyncClient):
    """GET /risk?bbox with fewer than 4 parts must return 422."""
    token = await register_and_login(client, "citizen")
    resp = await client.get("/risk?bbox=26.0,91.0,27.0", headers=auth_header(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_bbox_non_numeric_returns_422(client: AsyncClient):
    """GET /risk?bbox with non-numeric values must return 422."""
    token = await register_and_login(client, "citizen")
    resp = await client.get("/risk?bbox=26.0,abc,27.0,92.0", headers=auth_header(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_bbox_out_of_bounds_lat_returns_422(client: AsyncClient):
    """GET /risk?bbox with latitude > 90 must return 422."""
    token = await register_and_login(client, "citizen")
    resp = await client.get("/risk?bbox=200.0,91.0,27.0,92.0", headers=auth_header(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_horizon_unknown_unit_returns_422(client: AsyncClient):
    """GET /risk?horizon with unknown unit (e.g. 24x) must return 422."""
    token = await register_and_login(client, "citizen")
    resp = await client.get("/risk?horizon=24x", headers=auth_header(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_horizon_invalid_format_returns_422(client: AsyncClient):
    """GET /risk?horizon with non-integer value must return 422."""
    token = await register_and_login(client, "citizen")
    resp = await client.get("/risk?horizon=abch", headers=auth_header(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_post_out_of_bounds_lat_returns_422(client: AsyncClient):
    """POST /risk with lat > 90 must return 422 (Pydantic validation)."""
    token = await register_and_login(client, "officer")
    resp = await client.post("/risk", json={"lat": 200.0, "lng": 91.0},
                             headers=auth_header(token))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_risk_post_out_of_bounds_lng_returns_422(client: AsyncClient):
    """POST /risk with lng > 180 must return 422 (Pydantic validation)."""
    token = await register_and_login(client, "officer")
    resp = await client.post("/risk", json={"lat": 26.0, "lng": 250.0},
                             headers=auth_header(token))
    assert resp.status_code == 422


# --- 9. Dispatcher Redis resilience ---

@pytest.mark.asyncio
async def test_dispatcher_does_not_raise_when_redis_down():
    """
    dispatch_notification must never raise even when Redis is completely
    unavailable. The outer exception handler's redis.lpush is guarded.
    """
    from app.notifications.dispatcher import dispatch_notification

    with patch("app.notifications.dispatcher.get_provider") as mock_provider, \
         patch("app.notifications.dispatcher.redis_client") as mock_redis, \
         patch("app.notifications.dispatcher.async_session") as mock_session:

        mock_provider.return_value.send = AsyncMock(side_effect=RuntimeError("Provider down"))
        mock_redis.lpush = AsyncMock(side_effect=ConnectionError("Redis down"))

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.execute = AsyncMock(
            return_value=AsyncMock(scalar_one_or_none=AsyncMock(return_value=None))
        )
        mock_db.add = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_session.return_value = mock_db

        # Must not raise an exception even when provider & Redis fail
        await dispatch_notification(
            incident_id="test-001",
            recipient_id=1,
            channel="console",
            message="Test message",
            data_label="simulated",
        )


# --- 10. Priority weights from settings ---

def test_priority_weights_come_from_settings():
    """compute_priority uses settings.PRIORITY_W_* values."""
    from app.intelligence.priority import compute_priority

    result = compute_priority(
        risk_score=0.5,
        exposure_score=0.5,
        vulnerability_score=0.5,
        response_gap_score=0.5,
    )
    assert result["weights"]["risk"] == settings.PRIORITY_W_RISK
    assert result["weights"]["exposure"] == settings.PRIORITY_W_EXPOSURE
    assert result["weights"]["vulnerability"] == settings.PRIORITY_W_VULNERABILITY
    assert result["weights"]["response_gap"] == settings.PRIORITY_W_RESPONSE_GAP
    total = sum(result["weights"].values())
    assert abs(total - 1.0) < 0.001, f"Weights must sum to 1.0, got {total}"
