import json
from typing import Any

from fastapi import WebSocket
from app.core.redis import redis_client

CHANNEL = "crisiscore:status_updates"


class WSManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)

    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            self.active_connections[client_id] = [
                ws for ws in self.active_connections[client_id] if ws != websocket
            ]
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]

    async def broadcast(self, data: dict[str, Any]):
        message = json.dumps(data)
        await redis_client.publish(CHANNEL, message)

        for client_id, connections in list(self.active_connections.items()):
            dead = []
            for ws in connections:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[client_id].remove(ws)

    async def subscribe_and_forward(self, websocket: WebSocket, client_id: str):
        pubsub = redis_client.pubsub()
        await pubsub.subscribe(CHANNEL)
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    try:
                        await websocket.send_json(data)
                    except Exception:
                        break
        finally:
            await pubsub.unsubscribe(CHANNEL)


ws_manager = WSManager()
