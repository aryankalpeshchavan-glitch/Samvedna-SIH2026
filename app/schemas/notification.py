from datetime import datetime

from pydantic import BaseModel


class NotificationLogOut(BaseModel):
    id: str
    incident_id: str | None = None
    recipient_id: int
    channel: str
    payload: dict = {}
    data_label: str
    sent_at: datetime
    status: str

    model_config = {"from_attributes": True}
