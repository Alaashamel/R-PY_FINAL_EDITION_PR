from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class DoctorBase(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    specialization: str = Field(..., min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("specialization")
    @classmethod
    def normalize_specialization(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Specialization cannot be empty")
        return value


class DoctorCreate(DoctorBase):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=128)
    email: str = Field(..., max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if value.strip() != value or " " in value:
            raise ValueError("Password cannot contain spaces")
        if value.isalpha() or value.isdigit():
            raise ValueError("Password must contain both letters and numbers")
        return value

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class DoctorUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=2, max_length=50)
    last_name: Optional[str] = Field(None, min_length=2, max_length=50)
    specialization: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value

    @field_validator("specialization")
    @classmethod
    def normalize_specialization(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("Specialization cannot be empty")
        return value


class DoctorResponse(DoctorBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DoctorScheduleResponse(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    appointment_date: datetime
    status: str
    notes: Optional[str] = None
    created_at: datetime
