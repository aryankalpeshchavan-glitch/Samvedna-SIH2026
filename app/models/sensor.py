import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Float, Boolean, DateTime, ForeignKey, UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=False)
    sensor_type = Column(String(50), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    district = Column(String(50), nullable=True)
    state = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen = Column(DateTime, nullable=True)
    data_label = Column(String(20), default="synthetic", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sensor_id = Column(String(64), ForeignKey("sensors.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    rainfall_mm = Column(Float, nullable=True)
    soil_moisture_pct = Column(Float, nullable=True)
    tilt_degrees = Column(Float, nullable=True)
    temperature_c = Column(Float, nullable=True)
    battery_pct = Column(Float, nullable=True)
    data_label = Column(String(20), default="synthetic", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    sensor = relationship("Sensor", back_populates="readings")

    __table_args__ = (
        UniqueConstraint("sensor_id", "timestamp", name="uix_sensor_reading_time"),
    )
