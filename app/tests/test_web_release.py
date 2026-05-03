from fastapi.testclient import TestClient

from app.main import app
from app.version import VERSION_LABEL


def test_dashboard_renders_version_badge_and_release_popup(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert 'id="releaseModal"' in response.text
    assert "Neue Version verfuegbar" in response.text
    assert "Release" in response.text
    assert "stable" in response.text
    assert "Changelog" in response.text
