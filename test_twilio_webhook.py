from app import app


def test_twilio_webhook():
    client = app.test_client()
    response = client.post(
        "/ivr/incoming",
        data={"CallSid": "CA123456789", "From": "+254712345678", "To": "+13204313553"},
    )
    assert response.status_code == 200
    assert "text/xml" in response.headers.get("Content-Type", "")


def test_twilio_sms_webhook():
    client = app.test_client()
    response = client.post(
        "/sms/inbound/twilio",
        data={
            "MessageSid": "SM123456789",
            "From": "+254712345678",
            "To": "+13204313553",
            "Body": "Hello",
        },
    )
    assert response.status_code == 200
    assert "<Response>" in response.get_data(as_text=True)
