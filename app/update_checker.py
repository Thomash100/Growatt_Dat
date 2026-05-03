from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from typing import Any, Callable

from app.version import PROJECT_REPOSITORY, VERSION, VERSION_LABEL


FetchJson = Callable[[str, float], Any]


class UpdateCheckError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class UpdateCheckResult:
    enabled: bool
    status: str
    current_version: str
    current_version_label: str
    latest_version: str | None
    latest_version_label: str | None
    update_available: bool
    repository: str
    website: str
    release_url: str | None = None
    release_name: str | None = None
    published_at: str | None = None
    source: str | None = None
    changelog: str | None = None
    error_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class UpdateChecker:
    def __init__(
        self,
        repository: str = PROJECT_REPOSITORY,
        *,
        timeout_seconds: float = 4.0,
        enabled: bool = True,
        fetch_json: FetchJson | None = None,
    ) -> None:
        self.repository = repository.strip().strip("/")
        self.website = f"https://github.com/{self.repository}"
        self.timeout_seconds = timeout_seconds
        self.enabled = enabled
        self._fetch_json = fetch_json or fetch_json_from_url

    def check(self) -> UpdateCheckResult:
        if not self.enabled:
            return UpdateCheckResult(
                enabled=False,
                status="disabled",
                current_version=VERSION,
                current_version_label=VERSION_LABEL,
                latest_version=None,
                latest_version_label=None,
                update_available=False,
                repository=self.repository,
                website=self.website,
                error_status="update_check_disabled",
            )

        try:
            release = self._latest_release()
            latest_version = normalize_version(release["tag_name"])
            return UpdateCheckResult(
                enabled=True,
                status="ok",
                current_version=VERSION,
                current_version_label=VERSION_LABEL,
                latest_version=latest_version,
                latest_version_label=version_label(latest_version),
                update_available=compare_versions(latest_version, VERSION) > 0,
                repository=self.repository,
                website=self.website,
                release_url=release.get("html_url"),
                release_name=release.get("name") or release.get("tag_name"),
                published_at=release.get("published_at"),
                source=release.get("source"),
                changelog=release.get("body") or None,
            )
        except Exception as exc:
            return UpdateCheckResult(
                enabled=True,
                status="error",
                current_version=VERSION,
                current_version_label=VERSION_LABEL,
                latest_version=None,
                latest_version_label=None,
                update_available=False,
                repository=self.repository,
                website=self.website,
                error_status=str(exc),
            )

    def _latest_release(self) -> dict[str, Any]:
        release_url = f"https://api.github.com/repos/{self.repository}/releases/latest"
        try:
            release = self._fetch_json(release_url, self.timeout_seconds)
            if isinstance(release, dict) and release.get("tag_name"):
                release["source"] = "release"
                return release
        except UpdateCheckError:
            pass

        tags_url = f"https://api.github.com/repos/{self.repository}/tags?per_page=1"
        tags = self._fetch_json(tags_url, self.timeout_seconds)
        if isinstance(tags, list) and tags and isinstance(tags[0], dict) and tags[0].get("name"):
            tag_name = str(tags[0]["name"])
            return {
                "tag_name": tag_name,
                "name": tag_name,
                "html_url": f"https://github.com/{self.repository}/tree/{tag_name}",
                "published_at": None,
                "body": None,
                "source": "tag",
            }
        raise UpdateCheckError("no_github_release_or_tag_found")


def fetch_json_from_url(url: str, timeout_seconds: float) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "growatt-local-gateway-update-checker",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise UpdateCheckError(f"github_http_{exc.code}") from exc
    except urllib.error.URLError as exc:
        raise UpdateCheckError(f"github_unreachable: {exc.reason}") from exc
    except TimeoutError as exc:
        raise UpdateCheckError("github_timeout") from exc
    except json.JSONDecodeError as exc:
        raise UpdateCheckError("github_response_not_json") from exc


def normalize_version(value: str | None) -> str:
    normalized = (value or "").strip()
    if normalized.lower().startswith("version "):
        normalized = normalized.split(" ", 1)[1].strip()
    if normalized[:1].lower() == "v":
        normalized = normalized[1:]
    return normalized


def version_label(value: str | None) -> str | None:
    normalized = normalize_version(value)
    return None if not normalized else f"V{normalized}"


def compare_versions(left: str | None, right: str | None) -> int:
    left_parts = version_parts(left)
    right_parts = version_parts(right)
    max_len = max(len(left_parts), len(right_parts))
    left_parts += (0,) * (max_len - len(left_parts))
    right_parts += (0,) * (max_len - len(right_parts))
    return (left_parts > right_parts) - (left_parts < right_parts)


def version_parts(value: str | None) -> tuple[int, ...]:
    normalized = normalize_version(value)
    parts = [int(part) for part in re.findall(r"\d+", normalized)]
    return tuple(parts) if parts else (0,)
