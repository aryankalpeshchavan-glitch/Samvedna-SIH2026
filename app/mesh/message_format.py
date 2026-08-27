from datetime import datetime

from pydantic import BaseModel, Field


class MeshMessageFormat(BaseModel):
    message_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    origin_device_id: str
    payload: dict = {}
    hop_count: int = 0
    data_label: str = Field(default="synthetic")
    created_at: datetime = Field(default_factory=datetime.utcnow)
