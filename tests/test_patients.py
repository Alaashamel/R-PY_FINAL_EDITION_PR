def test_get_patients_authorized(client, user_token, sample_patient):
    response = client.get("/patients/", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()[0]["first_name"] == "Jane"


def test_create_patient_admin(client, admin_token):
    response = client.post(
        "/patients/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "Alice",
            "last_name": "Johnson",
            "username": "alicej",
            "password": "alicepass123",
            "email": "alice@email.com",
        },
    )
    assert response.status_code == 201
    assert response.json()["first_name"] == "Alice"


def test_create_patient_user_forbidden(client, user_token):
    response = client.post(
        "/patients/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "first_name": "Bob",
            "last_name": "Test",
            "username": "bobtest",
            "password": "bobpass123",
            "email": "bob@email.com",
        },
    )
    assert response.status_code == 403


def test_get_single_patient(client, user_token, sample_patient):
    response = client.get(
        f"/patients/{sample_patient.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["last_name"] == "Doe"
