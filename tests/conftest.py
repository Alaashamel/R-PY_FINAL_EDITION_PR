import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

from app.core.security import get_password_hash  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.database.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.doctor import Doctor  # noqa: E402
from app.models.patient import Patient  # noqa: E402

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def test_user(db):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture()
def test_admin(db):
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        is_active=True,
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


@pytest.fixture()
def test_doctor_user(db):
    doctor_user = User(
        username="doctor1",
        email="doctor@example.com",
        hashed_password=get_password_hash("doctorpass123"),
        is_active=True,
        is_doctor=True,
    )
    db.add(doctor_user)
    db.commit()
    db.refresh(doctor_user)
    return doctor_user


@pytest.fixture()
def sample_doctor(db, test_doctor_user):
    doctor = Doctor(
        user_id=test_doctor_user.id,
        first_name="John",
        last_name="Smith",
        specialization="Cardiology",
        phone="123456789",
        is_active=True,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor


@pytest.fixture()
def sample_patient(db, test_user):
    patient = Patient(
        user_id=test_user.id,
        first_name="Jane",
        last_name="Doe",
        phone="987654321",
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


@pytest.fixture()
def user_token(client, test_user):
    response = client.post("/auth/login", json={"username": "testuser", "password": "testpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def admin_token(client, test_admin):
    response = client.post("/auth/login", json={"username": "admin", "password": "adminpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def doctor_token(client, test_doctor_user):
    response = client.post("/auth/login", json={"username": "doctor1", "password": "doctorpass123"})
    assert response.status_code == 200
    return response.json()["access_token"]
