import sys
from pathlib import Path

# Ensure `import app` works when executed via:
#   docker compose exec app python scripts/seed.py
# In the container, this file lives at /app/scripts/seed.py.
# We need /app (so `import app` works) and also the parent repo root.
for p in [Path("/app"), Path(__file__).resolve().parents[2]]:
    p = p.resolve()
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.core.security import get_password_hash


from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient



def main():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin = User(
            username="admin",
            email="admin@hospital.com",
            hashed_password=get_password_hash("adminpass123"),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)

        doctor_user = User(
            username="dr_smith",
            email="smith@hospital.com",
            hashed_password=get_password_hash("doctorpass123"),
            is_active=True,
            is_doctor=True,
        )
        db.add(doctor_user)

        patient_user = User(
            username="patient1",
            email="patient@email.com",
            hashed_password=get_password_hash("patient123"),
            is_active=True,
        )
        db.add(patient_user)
        db.flush()

        doctor = Doctor(
            user_id=doctor_user.id,
            first_name="John",
            last_name="Smith",
            specialization="Cardiology",
            phone="+1234567890",
            is_active=True,
        )
        db.add(doctor)

        doctor2_user = User(
            username="dr_jones",
            email="jones@hospital.com",
            hashed_password=get_password_hash("doctorpass123"),
            is_active=True,
            is_doctor=True,
        )
        db.add(doctor2_user)
        db.flush()

        doctor2 = Doctor(
            user_id=doctor2_user.id,
            first_name="Emily",
            last_name="Jones",
            specialization="Neurology",
            phone="+1234567891",
            is_active=True,
        )
        db.add(doctor2)

        patient = Patient(
            user_id=patient_user.id,
            first_name="Jane",
            last_name="Doe",
            phone="+9876543210",
        )
        db.add(patient)

        db.commit()

        print("Seed data created.")
        print("Admin: admin / adminpass123")
        print("Doctor: dr_smith / doctorpass123")
        print("Patient: patient1 / patient123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
