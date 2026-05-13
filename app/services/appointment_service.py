from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session, joinedload

from app.core.redis_client import redis_client
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.schemas.appointment import AppointmentCreate
from app.utils.logger import logger


class AppointmentService:
    CACHE_PREFIX = "appointment"

    @staticmethod
    def _get_patient(db: Session, user_id: int) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.user_id == user_id).first()

    @staticmethod
    def _get_doctor(db: Session, user_id: int) -> Optional[Doctor]:
        return db.query(Doctor).filter(Doctor.user_id == user_id).first()

    @staticmethod
    def _resolve_name(appointment: Appointment) -> dict[str, Any]:
        data = {
            "id": appointment.id,
            "patient_id": appointment.patient_id,
            "doctor_id": appointment.doctor_id,
            "appointment_date": appointment.appointment_date,
            "status": appointment.status,
            "notes": appointment.notes,
            "created_at": appointment.created_at,
            "updated_at": appointment.updated_at,
            "patient_name": None,
            "doctor_name": None,
            "doctor_specialization": None,
        }
        if appointment.patient:
            data["patient_name"] = f"{appointment.patient.first_name} {appointment.patient.last_name}"
        if appointment.doctor:
            data["doctor_name"] = f"{appointment.doctor.first_name} {appointment.doctor.last_name}"
            data["doctor_specialization"] = appointment.doctor.specialization
        return data

    @staticmethod
    def create_appointment(db: Session, user_id: int, appointment_data: AppointmentCreate) -> Optional[Appointment]:
        patient = AppointmentService._get_patient(db, user_id)
        if not patient:
            logger.warning(f"No patient profile for user {user_id}")
            return None

        doctor = db.query(Doctor).filter(
            Doctor.id == appointment_data.doctor_id,
            Doctor.is_active.is_(True),
        ).first()
        if not doctor:
            raise ValueError("Doctor not found or inactive")

        existing = db.query(Appointment).filter(
            Appointment.doctor_id == appointment_data.doctor_id,
            Appointment.appointment_date == appointment_data.appointment_date,
            Appointment.status == AppointmentStatus.SCHEDULED,
        ).first()
        if existing:
            raise ValueError("Doctor already has an appointment at this time")

        db_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=appointment_data.doctor_id,
            appointment_date=appointment_data.appointment_date,
            notes=appointment_data.notes,
        )
        db.add(db_appointment)
        db.commit()
        db.refresh(db_appointment)
        db.refresh(db_appointment, attribute_names=["patient", "doctor"])

        redis_client.delete_pattern(f"{AppointmentService.CACHE_PREFIX}:*")
        logger.info(
            f"Appointment {db_appointment.id} booked: patient={patient.id}, doctor={doctor.id}, "
            f"date={appointment_data.appointment_date}"
        )

        return db_appointment

    @staticmethod
    def get_user_appointments(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Any]:
        patient = AppointmentService._get_patient(db, user_id)
        if patient:
            appointments = (
                db.query(Appointment)
                .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
                .filter(Appointment.patient_id == patient.id)
                .order_by(Appointment.appointment_date.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            appointments = []
        return [AppointmentService._resolve_name(a) for a in appointments]

    @staticmethod
    def get_doctor_appointments(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> list[Any]:
        doctor = AppointmentService._get_doctor(db, user_id)
        if doctor:
            appointments = (
                db.query(Appointment)
                .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
                .filter(Appointment.doctor_id == doctor.id)
                .order_by(Appointment.appointment_date.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            appointments = []
        return [AppointmentService._resolve_name(a) for a in appointments]

    @staticmethod
    def get_all_appointments(db: Session, skip: int = 0, limit: int = 100) -> list[Any]:
        cache_key = f"{AppointmentService.CACHE_PREFIX}:all:{skip}:{limit}"

        cached = redis_client.get(cache_key)
        if cached is not None:
            logger.info("Cache hit for all appointments")
            return cached

        appointments = (
            db.query(Appointment)
            .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
            .order_by(Appointment.appointment_date.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        result = [AppointmentService._resolve_name(a) for a in appointments]
        redis_client.set(cache_key, result, expire=300)
        return result

    @staticmethod
    def get_appointment(db: Session, appointment_id: int) -> Optional[Any]:
        appointment = (
            db.query(Appointment)
            .options(joinedload(Appointment.patient), joinedload(Appointment.doctor))
            .filter(Appointment.id == appointment_id)
            .first()
        )
        if not appointment:
            return None
        return AppointmentService._resolve_name(appointment)

    @staticmethod
    def update_appointment_status(
        db: Session,
        appointment_id: int,
        status: AppointmentStatus,
        doctor_user_id: int,
    ) -> Optional[Appointment]:
        appointment = (
            db.query(Appointment)
            .options(joinedload(Appointment.doctor))
            .filter(Appointment.id == appointment_id)
            .first()
        )
        if not appointment:
            return None

        doctor = AppointmentService._get_doctor(db, doctor_user_id)
        if not doctor:
            return None

        # Doctor can update only their own appointments
        if appointment.doctor_id != doctor.id:
            return None

        appointment.status = status
        db.commit()
        db.refresh(appointment)

        redis_client.delete_pattern(f"{AppointmentService.CACHE_PREFIX}:*")
        logger.info(
            f"Appointment {appointment_id} status updated to {status.value} by doctor_user_id={doctor_user_id}"
        )

        return appointment

    @staticmethod
    def cancel_appointment(db: Session, appointment_id: int, user_id: int, is_admin: bool = False) -> bool:
        appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
        if not appointment:
            return False

        if appointment.status != AppointmentStatus.SCHEDULED:
            return False

        patient = AppointmentService._get_patient(db, user_id)
        doctor = AppointmentService._get_doctor(db, user_id)

        is_owner = patient and appointment.patient_id == patient.id
        is_assigned_doctor = doctor and appointment.doctor_id == doctor.id

        if not (is_owner or is_assigned_doctor or is_admin):
            return False

        appointment.status = AppointmentStatus.CANCELLED
        db.commit()

        redis_client.delete_pattern(f"{AppointmentService.CACHE_PREFIX}:*")
        logger.info(f"Appointment {appointment_id} cancelled by user {user_id}")

        return True

    @staticmethod
    def get_scheduled_count(db: Session, doctor_id: int, appointment_date: datetime) -> int:
        return (
            db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.status == AppointmentStatus.SCHEDULED,
            )
            .count()
        )
