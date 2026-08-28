import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    severity = Column(Integer, default=1)
    status = Column(String(20), default="reported", nullable=False)
    data_label = Column(String(20), default="synthetic", nullable=False)
    photo_url = Column(String(512), nullable=True)
    idempotency_key = Column(String(128), unique=True, nullable=True, index=True)
    occurred_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


    reporter = relationship("User", back_populates="incidents")
    assignments = relationship("Assignment", back_populates="incident")
    notifications = relationship("NotificationLog", back_populates="incident")
