def test_live_health_does_not_require_database(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readiness_is_not_false_nba_ready_without_database_or_provider(client):
    response = client.get("/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["database"]["ready"] is False
    assert body["provider"]["ready"] is False
