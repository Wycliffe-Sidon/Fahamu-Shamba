from app import app


def test_ussd():
    client = app.test_client()
    response = client.post(
        "/ussd",
        data={
            "sessionId": "TEST123",
            "phoneNumber": "+254712345678",
            "text": "",
            "networkCode": "63902",
        },
    )
    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith("CON")


def test_ussd_with_input():
    client = app.test_client()
    response = client.post(
        "/ussd",
        data={
            "sessionId": "TEST123",
            "phoneNumber": "+254712345678",
            "text": "1",
            "networkCode": "63902",
        },
    )
    assert response.status_code == 200
    assert response.get_data(as_text=True).startswith("CON")
