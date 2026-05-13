def test_monitoring_health_public(client):
    response = client.get("/monitoring/health")
    assert response.status_code == 200
    assert "status" in response.json()


def test_recent_errors_requires_admin(client, user_token):
    response = client.get(
        "/monitoring/recent-errors",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403


def test_recent_errors_admin(client, admin_token):
    response = client.get(
        "/monitoring/recent-errors",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert "errors" in response.json()
