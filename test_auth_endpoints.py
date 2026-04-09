from app import app


def test_auth_pages_render():
    client = app.test_client()

    for path in ["/login", "/register", "/dashboard"]:
        response = client.get(path)
        assert response.status_code in {200, 302}


def test_register_rejects_missing_required_fields():
    client = app.test_client()

    response = client.post("/register", json={})

    assert response.status_code == 400
    assert "error" in response.get_json()
