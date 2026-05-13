from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_active_user, get_current_admin_user, get_current_doctor_user
from app.database.session import get_db
from app.models.appointment import AppointmentStatus
from app.models.user import User
from app.schemas.appointment import AppointmentCreate, AppointmentResponse, AppointmentUpdate
from app.services.appointment_service import AppointmentService
from app.services.patient_service import PatientService

router = APIRouter(prefix="/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    patient = PatientService.get_patient_by_user_id(db, current_user.id)
    if not patient:
        raise HTTPException(status_code=400, detail="Patient profile required to book appointments")

    try:
        appointment = AppointmentService.create_appointment(db, current_user.id, appointment_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not appointment:
        raise HTTPException(status_code=400, detail="Cannot create appointment")

    return AppointmentService.get_appointment(db, appointment.id)


@router.get("/", response_model=list[AppointmentResponse])
def get_my_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    if current_user.is_doctor:
        return AppointmentService.get_doctor_appointments(db, current_user.id, skip, limit)
    return AppointmentService.get_user_appointments(db, current_user.id, skip, limit)


@router.get("/all", response_model=list[AppointmentResponse])
def get_all_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> Any:
    return AppointmentService.get_all_appointments(db, skip, limit)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    appointment = AppointmentService.get_appointment(db, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    patient = PatientService.get_patient_by_user_id(db, current_user.id)
    if not current_user.is_admin and not current_user.is_doctor:
        if not patient or appointment["patient_id"] != patient.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this appointment")

    return appointment


@router.put("/{appointment_id}/status")
def update_appointment_status(
    appointment_id: int = Path(..., gt=0),
    appointment_status: AppointmentStatus = Query(..., alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_doctor_user),
):
    appointment = AppointmentService.update_appointment_status(
        db,
        appointment_id,
        appointment_status,
        doctor_user_id=current_user.id,
    )
    if not appointment:
        # For security, treat "not owned" as not found
        raise HTTPException(status_code=404, detail="Appointment not found")
    return {"message": f"Appointment status updated to {appointment_status.value}"}


@router.post("/{appointment_id}/cancel")
def cancel_appointment(
    appointment_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    cancelled = AppointmentService.cancel_appointment(
        db, appointment_id, current_user.id, current_user.is_admin
    )
    if not cancelled:
        raise HTTPException(status_code=400, detail="Cannot cancel appointment")
    return {"message": "Appointment cancelled"}
