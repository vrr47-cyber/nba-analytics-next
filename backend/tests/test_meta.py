def test_seasons_returns_unavailable_envelope(client):
    response = client.get("/api/v1/meta/seasons")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["coverage"]["is_publishable"] is False
    assert body["coverage"]["reason"] == "No validated season dataset is available."
    assert body["provenance"]["synthetic"] is False
