import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, ForeignKey, JSON,
)

from app.core.database import Base


class Resource(Base):
    __tablename__ = "resources"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String(20), default="available", nullable=False)
    data_label = Column(String(20), default="synthetic", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
