import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON
from app.core.database import Base


class ExposureZone(Base):
    """
    Represents exposure/impact data for a geographic location.
    Sourced from simulated/demo data; always marked with data_status.

    Population and infrastructure counts are stored here so the
    operational priority layer can compute exposure without calling
    an external API.
    """
    __tablename__ = "exposure_zones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(128), nullable=True)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius_km = Column(Float, default=5.0)

    # Human exposure
    population = Column(Integer, default=0)
    households = Column(Integer, default=0)

    # Critical infrastructure
    schools = Column(Integer, default=0)
    hospitals = Column(Integer, default=0)
    critical_roads = Column(Integer, default=0)

    # Vulnerability metadata
    distance_to_hospital_km = Column(Float, nullable=True)
    has_early_warning = Column(Boolean, default=False)
    road_access_quality = Column(String(20), default="moderate")  # good | moderate | poor

    # Data provenance — always transparent
    data_status = Column(String(20), default="simulated", nullable=False)
    source = Column(String(256), nullable=True)
    extra = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
