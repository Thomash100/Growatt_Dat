from app.update_checker import UpdateCheckError, UpdateChecker, compare_versions, normalize_version, version_label
from app.version import VERSION, VERSION_LABEL


def test_version_helpers_normalize_and_compare():
    assert normalize_version("v0.001.4") == "0.001.4"
    assert version_label("0.001.4") == "V0.001.4"
    assert compare_versions("v0.001.10", "V0.001.4") > 0
    assert compare_versions("0.001.4", "0.001.4") == 0
    assert compare_versions("0.001.3", "0.001.4") < 0


def test_update_checker_detects_newer_github_release():
    def fetch_json(url: str, timeout_seconds: float):
        assert timeout_seconds == 1.0
        assert url.endswith("/releases/latest")
        return {
            "tag_name": "v9.0.0",
            "name": "V9.0.0",
            "html_url": "https://example.invalid/release",
            "published_at": "2026-05-03T10:00:00Z",
            "body": "Example changelog",
        }

    result = UpdateChecker("Owner/Repo", timeout_seconds=1.0, fetch_json=fetch_json).check()

    assert result.status == "ok"
    assert result.current_version == VERSION
    assert result.current_version_label == VERSION_LABEL
    assert result.latest_version == "9.0.0"
    assert result.latest_version_label == "V9.0.0"
    assert result.update_available is True
    assert result.source == "release"
    assert result.changelog == "Example changelog"


def test_update_checker_falls_back_to_latest_tag():
    def fetch_json(url: str, timeout_seconds: float):
        if url.endswith("/releases/latest"):
            raise UpdateCheckError("github_http_404")
        return [{"name": "v0.001.4"}]

    result = UpdateChecker("Owner/Repo", fetch_json=fetch_json).check()

    assert result.status == "ok"
    assert result.latest_version == "0.001.4"
    assert result.update_available is False
    assert result.source == "tag"


def test_update_checker_can_be_disabled():
    result = UpdateChecker("Owner/Repo", enabled=False).check()

    assert result.enabled is False
    assert result.status == "disabled"
    assert result.update_available is False
    assert result.error_status == "update_check_disabled"
