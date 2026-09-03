from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Volunteer(Base):
    __tablename__ = "volunteers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    skills = Column(String(512), default="")
    lat = Column(Float, default=0.0)
    lng = Column(Float, default=0.0)
    availability_status = Column(String(20), default="available", nullable=False)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=True)

    assignments = relationship("Assignment", back_populates="volunteer")
