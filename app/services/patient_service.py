from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.redis_client import redis_client
from app.core.security import get_password_hash
from app.models.patient import Patient
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate
from app.utils.logger import logger
from app.utils.serialization import to_plain_dict


class PatientService:
    CACHE_PREFIX = "patient"

    @staticmethod
    def get_patients(db: Session, skip: int = 0, limit: int = 100) -> list[Any]:
        cache_key = f"{PatientService.CACHE_PREFIX}:list:{skip}:{limit}"

        cached = redis_client.get(cache_key)
        if cached is not None:
            logger.info("Cache hit for patients list")
            return cached

        patients = db.query(Patient).offset(skip).limit(limit).all()
        redis_client.set(cache_key, [to_plain_dict(p) for p in patients], expire=300)
        return patients

    @staticmethod
    def get_patient(db: Session, patient_id: int) -> Optional[Any]:
        cache_key = f"{PatientService.CACHE_PREFIX}:{patient_id}"

        cached = redis_client.get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for patient {patient_id}")
            return cached

        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            redis_client.set(cache_key, to_plain_dict(patient), expire=300)

        return patient

    @staticmethod
    def get_patient_by_user_id(db: Session, user_id: int) -> Optional[Patient]:
        return db.query(Patient).filter(Patient.user_id == user_id).first()

    @staticmethod
    def create_patient(db: Session, patient_data: PatientCreate, admin_id: int) -> Patient:
        existing_user = db.query(User).filter(
            (User.username == patient_data.username) | (User.email == patient_data.email)
        ).first()
        if existing_user:
            raise ValueError("Username or email already registered")

        user = User(
            username=patient_data.username,
            email=patient_data.email,
            hashed_password=get_password_hash(patient_data.password),
            is_active=True,
        )
        db.add(user)
        db.flush()

        db_patient = Patient(
            user_id=user.id,
            first_name=patient_data.first_name,
            last_name=patient_data.last_name,
            phone=patient_data.phone,
            date_of_birth=patient_data.date_of_birth,
        )
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)

        redis_client.delete_pattern(f"{PatientService.CACHE_PREFIX}:*")
        logger.info(f"Patient created by admin {admin_id}: {patient_data.first_name} {patient_data.last_name}")

        return db_patient

    @staticmethod
    def update_patient(db: Session, patient_id: int, patient_data: PatientUpdate, admin_id: int) -> Optional[Patient]:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None

        update_data = patient_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(patient, field, value)

        db.commit()
        db.refresh(patient)

        redis_client.delete_pattern(f"{PatientService.CACHE_PREFIX}:*")
        logger.info(f"Patient {patient_id} updated by admin {admin_id}")

        return patient

    @staticmethod
    def delete_patient(db: Session, patient_id: int, admin_id: int) -> bool:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return False

        db.delete(patient)
        db.commit()

        redis_client.delete_pattern(f"{PatientService.CACHE_PREFIX}:*")
        logger.info(f"Patient {patient_id} deleted by admin {admin_id}")

        return True
