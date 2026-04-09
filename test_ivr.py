from app import app


def test_ivr_incoming():
    client = app.test_client()
    response = client.post(
        "/ivr/incoming",
        data={"CallSid": "CA123456789", "From": "+254712345678", "To": "+13204313553"},
    )
    assert response.status_code == 200
    assert "<Response>" in response.get_data(as_text=True)


def test_ivr_menu():
    client = app.test_client()
    response = client.post("/ivr/menu?lang=en", data={"CallSid": "CA123456789", "Digits": "1"})
    assert response.status_code == 200
    assert "<Response>" in response.get_data(as_text=True)
