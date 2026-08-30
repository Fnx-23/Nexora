"""Health endpoint tests."""


def test_healthz_reports_healthy(api_client, db):
    response = api_client.get("/healthz/")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["components"]["database"]["healthy"] is True
