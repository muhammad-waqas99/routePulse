"""Health endpoint tests."""

from __future__ import annotations


def test_health_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200

    body = response.json()
    assert body["success"] is True
    assert body["status"] == "ok"
    assert body["service"] == "routepulse-backend"
    assert "version" in body
