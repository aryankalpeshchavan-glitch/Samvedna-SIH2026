import uuid
from datetime import datetime

from sqlalchemy import (
    Column, Integer, DateTime, ForeignKey, String,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(String(36), ForeignKey("incidents.id"), nullable=False)
    volunteer_id = Column(Integer, ForeignKey("volunteers.id"), nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    acked_at = Column(DateTime, nullable=True)
    sla_deadline = Column(DateTime, nullable=False)

    incident = relationship("Incident", back_populates="assignments")
    volunteer = relationship("Volunteer", back_populates="assignments")
