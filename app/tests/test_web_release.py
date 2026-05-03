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


def test_update_page_renders_without_network_when_disabled(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/update")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert "Update-Status" in response.text
    assert "Update-Pruefung ist deaktiviert" in response.text


def test_integrations_page_renders(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/integrations")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert "Integrationen" in response.text
    assert "192.168.178.0/24" in response.text
