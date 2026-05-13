from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    doctor_id: int = Field(..., gt=0)
    appointment_date: datetime
    notes: Optional[str] = Field(None, max_length=500)

    @field_validator("appointment_date")
    @classmethod
    def validate_future_date(cls, value: datetime) -> datetime:
        if value < datetime.now(value.tzinfo):
            raise ValueError("Appointment date must be in the future")
        return value


class AppointmentUpdate(BaseModel):
    status: AppointmentStatus


class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None

    class Config:
        from_attributes = True
