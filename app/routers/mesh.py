from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.models.user import User
from app.schemas.mesh import MeshMessageCreate, MeshSimulateResponse
from app.mesh.relay_mock import simulate_relay

router = APIRouter(prefix="/mesh", tags=["mesh"])


@router.post("/simulate", response_model=MeshSimulateResponse)
async def mesh_simulate(
    data: MeshMessageCreate,
    current_user: User = Depends(get_current_user),
):
    result = await simulate_relay(
        origin_device_id=data.origin_device_id,
        payload=data.payload,
        data_label=data.data_label,
    )
    return result
