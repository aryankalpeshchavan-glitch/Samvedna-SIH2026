from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(15), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    name = Column(String(120), nullable=False)
    role = Column(String(20), nullable=False, default="citizen")
    lang = Column(String(5), default="en")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    incidents = relationship("Incident", back_populates="reporter")
