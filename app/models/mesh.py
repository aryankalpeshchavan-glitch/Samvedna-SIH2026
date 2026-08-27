import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, DateTime, JSON,
)

from app.core.database import Base


class MeshMessage(Base):
    __tablename__ = "mesh_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    origin_device_id = Column(String(64), nullable=False)
    payload = Column(JSON, default={})
    hop_count = Column(Integer, default=0)
    data_label = Column(String(20), default="synthetic", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
