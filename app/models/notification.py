import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, DateTime, ForeignKey, JSON,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationLog(Base):
    __tablename__ = "notifications_log"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=True)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel = Column(String(20), nullable=False)
    payload = Column(JSON, default={})
    data_label = Column(String(20), default="synthetic", nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    status = Column(String(20), default="queued", nullable=False)

    incident = relationship("Incident", back_populates="notifications")
