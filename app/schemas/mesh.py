from pydantic import BaseModel, Field


class MeshMessageCreate(BaseModel):
    origin_device_id: str = Field(..., max_length=64)
    payload: dict = {}
    data_label: str = Field(default="synthetic", pattern=r"^(live|synthetic|replayed)$")


class MeshSimulateResponse(BaseModel):
    message_id: str
    relay_path: list[str]
    hops_completed: int
    data_label: str
