"""
Mesh relay MOCK for demo purposes.
NOT a real BLE/Bridgefy integration — simulates store-and-forward relay.
TODO(Anjishnu): Bridgefy/BLE mesh is stub-only; do not let this block Levels 1-3
(LAN/WAN push, low-bandwidth text mode, SMS/USSD). If relay becomes flaky, leave TODO
and keep Levels 1-3 as primary. Current stub is stable for demo (test: test_api:test_mesh_simulate).
"""
import asyncio
from datetime import datetime
from uuid import uuid4

from app.core.database import async_session
from app.models.mesh import MeshMessage
from app.schemas.mesh import MeshSimulateResponse


async def simulate_relay(
    origin_device_id: str,
    payload: dict,
    data_label: str = "synthetic",
    hops: int = 2,
) -> MeshSimulateResponse:
    relay_path = [f"device_{origin_device_id}"]

    for hop in range(hops):
        await asyncio.sleep(0.05)
        relay_path.append(f"relay_node_{hop + 1}")

    async with async_session() as db:
        mesh_msg = MeshMessage(
            id=str(uuid4()),
            origin_device_id=origin_device_id,
            payload=payload,
            hop_count=hops,
            data_label=data_label,
            created_at=datetime.utcnow(),
        )
        db.add(mesh_msg)
        await db.commit()

    return MeshSimulateResponse(
        message_id=str(uuid4()),
        relay_path=relay_path,
        hops_completed=hops,
        data_label=data_label,
    )
