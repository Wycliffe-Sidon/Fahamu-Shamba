from app import app
import uuid


def test_registration():
    client = app.test_client()
    unique = uuid.uuid4().hex
    response = client.post(
        "/register",
        json={
            "email": f"test_auth_{unique}@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
            "phone_number": f"+2547{unique[:8]}",
            "county": "Nairobi",
            "language_preference": "en",
            "newsletter_subscribed": True,
            "terms": True,
        },
    )
    assert response.status_code in {200, 201}


def test_login():
    client = app.test_client()
    unique = uuid.uuid4().hex
    email = f"test_login_{unique}@example.com"
    client.post(
        "/register",
        json={
            "email": email,
            "first_name": "Jane",
            "last_name": "Doe",
            "password": "testpassword123",
            "confirm_password": "testpassword123",
            "phone_number": f"+2547{unique[:8]}",
            "county": "Nakuru",
            "language_preference": "en",
            "terms": True,
        },
    )
    response = client.post(
        "/login",
        json={"identifier": email, "password": "testpassword123"},
    )
    assert response.status_code == 200


def test_invalid_login():
    client = app.test_client()
    response = client.post(
        "/login",
        json={"identifier": "missing@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_duplicate_registration():
    client = app.test_client()
    unique = uuid.uuid4().hex
    payload = {
        "email": f"test_duplicate_{unique}@example.com",
        "first_name": "Janet",
        "last_name": "Smith",
        "password": "anotherpassword123",
        "confirm_password": "anotherpassword123",
        "phone_number": f"+2547{unique[:8]}",
        "county": "Kiambu",
        "language_preference": "en",
        "terms": True,
    }
    first = client.post("/register", json=payload)
    second = client.post("/register", json=payload)
    assert first.status_code in {200, 201}
    assert second.status_code == 409
