def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "newpass123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "hashed_password" not in data


def test_register_duplicate_user(client, test_user):
    response = client.post(
        "/auth/register",
        json={"username": "testuser", "email": "other@example.com", "password": "newpass123"},
    )
    assert response.status_code == 400


def test_register_rejects_weak_password(client):
    response = client.post(
        "/auth/register",
        json={"username": "weakuser", "email": "weak@example.com", "password": "password"},
    )
    assert response.status_code == 422


def test_login_success(client, test_user):
    response = client.post("/auth/login", json={"username": "testuser", "password": "testpass123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_fail(client, test_user):
    response = client.post("/auth/login", json={"username": "testuser", "password": "wrongpass123"})
    assert response.status_code == 401


def test_read_current_user(client, user_token):
    response = client.get("/users/me", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
