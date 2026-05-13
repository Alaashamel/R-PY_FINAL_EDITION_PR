def test_get_doctors_unauthorized(client):
    response = client.get("/doctors/")
    assert response.status_code == 403


def test_get_doctors_authorized(client, user_token, sample_doctor):
    response = client.get("/doctors/", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()[0]["first_name"] == "John"


def test_create_doctor_admin(client, admin_token):
    response = client.post(
        "/doctors/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "first_name": "Sarah",
            "last_name": "Connor",
            "specialization": "Neurology",
            "username": "drsarah",
            "password": "sarahpass123",
            "email": "sarah@hospital.com",
        },
    )
    assert response.status_code == 201
    assert response.json()["specialization"] == "Neurology"


def test_create_doctor_user_forbidden(client, user_token):
    response = client.post(
        "/doctors/",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "first_name": "Sarah",
            "last_name": "Connor",
            "specialization": "Neurology",
            "username": "drsarah",
            "password": "sarahpass123",
            "email": "sarah@hospital.com",
        },
    )
    assert response.status_code == 403


def test_get_doctor_by_id(client, user_token, sample_doctor):
    response = client.get(
        f"/doctors/{sample_doctor.id}",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 200
    assert response.json()["specialization"] == "Cardiology"
