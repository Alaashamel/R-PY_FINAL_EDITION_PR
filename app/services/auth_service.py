from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.patient import Patient
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.logger import logger


class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserCreate, is_doctor: bool = False, is_admin: bool = False) -> User:
        email = str(user_data.email).lower()
        existing_user = (
            db.query(User)
            .filter((User.username == user_data.username) | (User.email == email))
            .first()
        )

        if existing_user:
            logger.warning(f"Registration failed - user exists: {user_data.username}")
            raise ValueError("Username or email already registered")

        db_user = User(
            email=email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            is_doctor=is_doctor,
            is_admin=is_admin,
        )

        db.add(db_user)
        db.flush()  # Get user ID before commit

        # Auto-create patient profile for regular users (not admin/doctor)
        if not is_doctor and not is_admin:
            patient = Patient(
                user_id=db_user.id,
                first_name=user_data.first_name or user_data.username,
                last_name=user_data.last_name or "Patient",
                phone=None,
            )
            db.add(patient)
            logger.info(f"Patient profile created for user {db_user.id}")

        db.commit()
        db.refresh(db_user)

        logger.info(f"New user registered: {user_data.username} (doctor={is_doctor}, admin={is_admin})")
        return db_user

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            logger.warning(f"Failed login attempt for user: {username}")
            return None
        logger.info(f"User logged in: {username}")
        return user

    @staticmethod
    def create_user_token(user: User) -> str:
        return create_access_token(data={"sub": user.username})
