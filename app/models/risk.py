import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Integer, DateTime, JSON,
)

from app.core.database import Base


class RiskZone(Base):
    __tablename__ = "risk_zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    risk_score = Column(Float, nullable=False)
    horizon_hours = Column(Integer, nullable=False)
    top_features = Column(JSON, default={})
    data_label = Column(String(20), default="synthetic", nullable=False)
    computed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)
