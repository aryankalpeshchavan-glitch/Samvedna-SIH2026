import json
from unittest.mock import patch, AsyncMock
import pytest
from httpx import AsyncClient

from app.main import app
from app.matching.queue import enqueue_matching_job
from tests.test_api import auth_header, register_and_login, client, setup_db


@pytest.mark.asyncio
async def test_enqueue_matching_job_payload():
    with patch("app.matching.queue.get_redis") as mock_get_redis:
        mock_redis = AsyncMock()
        mock_get_redis.return_value = mock_redis
        
        success = await enqueue_matching_job("test-incident-123")
        assert success is True
        
        # Verify it was called with the right queue name
        mock_redis.lpush.assert_called_once()
        args, kwargs = mock_redis.lpush.call_args
        assert args[0] == "matching_queue"
        
        # Verify JSON serializable payload
        payload = json.loads(args[1])
        assert payload["incident_id"] == "test-incident-123"
        assert payload["action"] == "match"
        assert "timestamp" in payload


@pytest.mark.asyncio
async def test_enqueue_matching_job_redis_unavailable():
    with patch("app.matching.queue.get_redis") as mock_get_redis:
        mock_get_redis.side_effect = Exception("Redis connection refused")
        
        success = await enqueue_matching_job("test-incident-123")
        assert success is False


@pytest.mark.asyncio
async def test_incident_creation_enqueues_job(client: AsyncClient):
    with patch("app.routers.incidents.enqueue_matching_job", new_callable=AsyncMock) as mock_enqueue:
        mock_enqueue.return_value = True
        
        token = await register_and_login(client, "officer")
        resp = await client.post("/incidents", json={
            "type": "flood",
            "description": "Test matching queue",
            "lat": 26.0,
            "lng": 91.0,
            "severity": 2
        }, headers=auth_header(token))
        
        assert resp.status_code == 201
        incident_id = resp.json()["id"]
        
        # Ensure it was called with the new incident_id
        mock_enqueue.assert_called_with(incident_id)
