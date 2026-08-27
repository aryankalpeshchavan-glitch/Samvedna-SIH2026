from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Role(str, Enum):
    citizen = "citizen"
    volunteer = "volunteer"
    officer = "officer"
    admin = "admin"


class UserCreate(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1, max_length=120)
    role: Role = Role.citizen
    lang: str = Field(default="en", max_length=5)


class UserLogin(BaseModel):
    phone: str
    password: str


class UserOut(BaseModel):
    id: int
    phone: str
    name: str
    role: Role
    lang: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Role
