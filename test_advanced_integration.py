from app import app


def test_all_services_health():
    client = app.test_client()
    endpoints = [
        "/health",
        "/deployment/summary",
        "/weather/nairobi",
        "/market",
        "/satellite/nairobi",
    ]
    results = {}
    for endpoint in endpoints:
        response = client.get(endpoint)
        results[endpoint] = response.status_code
        assert response.status_code == 200
    assert results["/health"] == 200
