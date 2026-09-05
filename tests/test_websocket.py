"""WebSocket reconnect correctness test."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.realtime.ws_manager import WSManager


@pytest.mark.asyncio
async def test_ws_manager_reconnect_receives_current_state():
    manager = WSManager()
    mock_ws = AsyncMock()
    mock_ws.send_json = AsyncMock()

    await manager.connect(mock_ws, "client_1")
    assert "client_1" in manager.active_connections

    manager.disconnect(mock_ws, "client_1")
    assert "client_1" not in manager.active_connections

    mock_ws2 = AsyncMock()
    await manager.connect(mock_ws2, "client_1")
    assert "client_1" in manager.active_connections

    with patch("app.realtime.ws_manager.redis_client.publish", new_callable=AsyncMock):
        await manager.broadcast({"incident_id": "test", "status": "verified"})
    mock_ws2.send_json.assert_called_once_with({"incident_id": "test", "status": "verified"})


@pytest.mark.asyncio
async def test_ws_broadcast_does_not_crash_on_dead_connection():
    manager = WSManager()
    dead_ws = AsyncMock()
    dead_ws.send_json = AsyncMock(side_effect=Exception("Connection closed"))

    alive_ws = AsyncMock()
    alive_ws.send_json = AsyncMock()

    await manager.connect(dead_ws, "c1")
    await manager.connect(alive_ws, "c1")

    with patch("app.realtime.ws_manager.redis_client.publish", new_callable=AsyncMock):
        await manager.broadcast({"test": True})

    dead_ws.send_json.assert_called_once()
    alive_ws.send_json.assert_called_once_with({"test": True})
    assert dead_ws not in manager.active_connections["c1"]

