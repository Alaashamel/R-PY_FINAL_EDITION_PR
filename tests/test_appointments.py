from datetime import datetime, timedelta


def test_book_appointment(client, user_token, sample_patient, sample_doctor):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    response = client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "doctor_id": sample_doctor.id,
            "appointment_date": future_date,
            "notes": "Checkup",
        },
    )
    assert response.status_code == 201
    assert response.json()["doctor_name"] is not None


def test_double_booking_rejected(client, user_token, sample_patient, sample_doctor):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    response = client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    assert response.status_code == 400


def test_get_my_appointments(client, user_token, sample_patient, sample_doctor):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    response = client.get("/appointments/", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_doctor_schedule(client, doctor_token, sample_doctor, sample_patient, test_user):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    patient_token = client.post("/auth/login", json={"username": "testuser", "password": "testpass123"}).json()["access_token"]
    client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    response = client.get("/appointments/", headers={"Authorization": f"Bearer {doctor_token}"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_cancel_appointment(client, user_token, sample_patient, sample_doctor):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    created = client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    appt_id = created.json()["id"]
    response = client.post(
        f"/appointments/{appt_id}/cancel",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200


def test_appointment_requires_patient_profile(client, user_token, sample_doctor):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    response = client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    assert response.status_code == 400


def test_update_appointment_status_doctor(client, doctor_token, sample_doctor, sample_patient, test_user):
    future_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    patient_token = client.post("/auth/login", json={"username": "testuser", "password": "testpass123"}).json()["access_token"]
    created = client.post(
        "/appointments/",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={"doctor_id": sample_doctor.id, "appointment_date": future_date},
    )
    appt_id = created.json()["id"]
    response = client.put(
        f"/appointments/{appt_id}/status?status=completed",
        headers={"Authorization": f"Bearer {doctor_token}"},
    )
    assert response.status_code == 200
