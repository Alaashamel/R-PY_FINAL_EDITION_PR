from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.redis_client import redis_client
from app.core.security import get_password_hash
from app.models.doctor import Doctor
from app.models.user import User
from app.schemas.doctor import DoctorCreate, DoctorUpdate
from app.utils.logger import logger
from app.utils.serialization import to_plain_dict


class DoctorService:
    CACHE_PREFIX = "doctor"

    @staticmethod
    def get_doctors(db: Session, skip: int = 0, limit: int = 100) -> list[Any]:
        cache_key = f"{DoctorService.CACHE_PREFIX}:list:{skip}:{limit}"

        cached = redis_client.get(cache_key)
        if cached is not None:
            logger.info("Cache hit for doctors list")
            return cached

        doctors = (
            db.query(Doctor)
            .filter(Doctor.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )
        redis_client.set(cache_key, [to_plain_dict(d) for d in doctors], expire=300)
        return doctors

    @staticmethod
    def get_doctor(db: Session, doctor_id: int) -> Optional[Any]:
        cache_key = f"{DoctorService.CACHE_PREFIX}:{doctor_id}"

        cached = redis_client.get(cache_key)
        if cached is not None:
            logger.info(f"Cache hit for doctor {doctor_id}")
            return cached

        doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_active.is_(True)).first()
        if doctor:
            redis_client.set(cache_key, to_plain_dict(doctor), expire=300)

        return doctor

    @staticmethod
    def create_doctor(db: Session, doctor_data: DoctorCreate, admin_id: int) -> Doctor:
        existing_user = db.query(User).filter(
            (User.username == doctor_data.username) | (User.email == doctor_data.email)
        ).first()
        if existing_user:
            raise ValueError("Username or email already registered")

        user = User(
            username=doctor_data.username,
            email=doctor_data.email,
            hashed_password=get_password_hash(doctor_data.password),
            is_active=True,
            is_doctor=True,
        )
        db.add(user)
        db.flush()

        db_doctor = Doctor(
            user_id=user.id,
            first_name=doctor_data.first_name,
            last_name=doctor_data.last_name,
            specialization=doctor_data.specialization,
            phone=doctor_data.phone,
        )
        db.add(db_doctor)
        db.commit()
        db.refresh(db_doctor)

        redis_client.delete_pattern(f"{DoctorService.CACHE_PREFIX}:*")
        logger.info(f"Doctor created by admin {admin_id}: {doctor_data.first_name} {doctor_data.last_name}")

        return db_doctor

    @staticmethod
    def update_doctor(db: Session, doctor_id: int, doctor_data: DoctorUpdate, admin_id: int) -> Optional[Doctor]:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return None

        update_data = doctor_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(doctor, field, value)

        db.commit()
        db.refresh(doctor)

        redis_client.delete_pattern(f"{DoctorService.CACHE_PREFIX}:*")
        logger.info(f"Doctor {doctor_id} updated by admin {admin_id}")

        return doctor

    @staticmethod
    def delete_doctor(db: Session, doctor_id: int, admin_id: int) -> bool:
        doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return False

        doctor.is_active = False
        db.commit()

        redis_client.delete_pattern(f"{DoctorService.CACHE_PREFIX}:*")
        logger.info(f"Doctor {doctor_id} deactivated by admin {admin_id}")

        return True
