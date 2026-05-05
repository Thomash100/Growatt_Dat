from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app
from app.version import VERSION_LABEL


def test_dashboard_renders_version_badge_and_release_popup(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert 'id="releaseModal"' in response.text
    assert 'id="updateIndicator" hidden aria-hidden="true"' in response.text
    assert f"/static/app.js?v={VERSION_LABEL}" in response.text
    assert f"/static/style.css?v={VERSION_LABEL}" in response.text
    assert "Neue Version verfuegbar" in response.text
    assert "Release" in response.text
    assert "stable" in response.text
    assert "Changelog" in response.text


def test_hidden_attribute_is_not_overridden_by_component_display_css():
    css = Path("app/web/static/style.css").read_text(encoding="utf-8")

    assert "[hidden]" in css
    assert "display: none !important" in css


def test_update_page_renders_without_network_when_disabled(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/update")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert "Update-Status" in response.text
    assert "Update-Pruefung ist deaktiviert" in response.text
    assert "Web-Update aktiviert" in response.text
    assert "Web-Update installieren" in response.text


def test_update_page_hides_token_field_when_not_required(monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")
    monkeypatch.setenv("WEB_UPDATE_ENABLED", "true")
    monkeypatch.setenv("WEB_UPDATE_TOKEN_REQUIRED", "false")
    monkeypatch.setenv("WEB_UPDATE_WORKDIR", str(tmp_path))
    monkeypatch.setenv("WEB_UPDATE_RUN_DOCKER_COMPOSE", "false")

    with TestClient(app) as client:
        response = client.get("/update")

    assert response.status_code == 200
    assert 'id="webUpdateToken"' not in response.text
    assert "Token ist deaktiviert" in response.text


def test_integrations_page_renders(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/integrations")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert "Integrationen" in response.text
    assert "Zusatz-Shellys" in response.text
    assert "192.168.178.0/24" in response.text


def test_statistics_page_renders(monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")

    with TestClient(app) as client:
        response = client.get("/statistics")

    assert response.status_code == 200
    assert VERSION_LABEL in response.text
    assert "Langzeit" in response.text
    assert "Tageswerte" in response.text


def test_web_update_rejects_invalid_token(monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("UPDATE_CHECK_ENABLED", "false")
    monkeypatch.setenv("WEB_UPDATE_ENABLED", "true")
    monkeypatch.setenv("WEB_UPDATE_TOKEN", "example-update-token-123")
    monkeypatch.setenv("WEB_UPDATE_WORKDIR", str(tmp_path))
    monkeypatch.setenv("WEB_UPDATE_RUN_DOCKER_COMPOSE", "false")

    with TestClient(app) as client:
        response = client.post("/api/update/install", json={"token": "wrong"})

    assert response.status_code == 403
    assert response.json()["detail"] == "invalid_update_token"
