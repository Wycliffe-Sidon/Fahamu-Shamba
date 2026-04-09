#!/usr/bin/env python3

import os

from app import app


def test_sms_send_endpoint_accepts_mock_request():
    client = app.test_client()
    original = os.environ.get("USE_MOCK_DATA")
    os.environ["USE_MOCK_DATA"] = "true"

    try:
        response = client.post(
            "/sms/send",
            json={
                "phone": "+254700000003",
                "message": "Hello farmer",
                "provider": "africastalking",
            },
        )
    finally:
        if original is None:
            os.environ.pop("USE_MOCK_DATA", None)
        else:
            os.environ["USE_MOCK_DATA"] = original

    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_twilio_sms_webhook_returns_twiml():
    client = app.test_client()

    response = client.post(
        "/sms/inbound/twilio",
        data={"From": "+254700000003", "Body": "What should I plant in Kitui?"},
    )

    assert response.status_code == 200
    assert "<Response>" in response.get_data(as_text=True)


def test_ivr_entrypoint_returns_twiml():
    client = app.test_client()

    response = client.post("/ivr/incoming", data={"From": "+254700000003", "CallSid": "CA123"})

    assert response.status_code == 200
    assert "<Gather" in response.get_data(as_text=True)
