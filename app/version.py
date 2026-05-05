VERSION = "0.001.11"
VERSION_LABEL = f"V{VERSION}"
RELEASE_CHANNEL = "stable"
PROJECT_REPOSITORY = "Thomash100/Growatt_Dat"
PROJECT_WEBSITE = "https://github.com/Thomash100/Growatt_Dat"

RELEASE_NOTES = {
    "de": {
        "title": "Neue Version verfuegbar",
        "next_release_title": "Was ist neu in dieser Version",
        "changelog_title": "Changelog",
        "groups": [
            {
                "title": "New Features",
                "icon": "*",
                "changes": [
                    "Web-Update-Git-Befehle markieren das Arbeitsverzeichnis als safe.directory.",
                    "Statische Webdateien werden mit Versionsparameter geladen, damit alte Browser-Caches den Update-Hinweis nicht festhalten.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Update-Indicator wird vor jeder Pruefung aktiv ausgeblendet und nur bei echter neuer Version wieder eingeblendet.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Web-Update scheitert im Docker-Mount nicht mehr am Git-Fehler dubious ownership / exit 128.",
                ],
            },
        ],
    },
    "en": {
        "title": "New version available",
        "next_release_title": "What is new in this version",
        "changelog_title": "Changelog",
        "groups": [
            {
                "title": "New Features",
                "icon": "*",
                "changes": [
                    "Web update Git commands mark the working directory as safe.directory.",
                    "Static web files are loaded with a version parameter so old browser caches cannot keep the update hint stale.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "The update indicator is actively hidden before every check and only shown again for a real newer version.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Web update no longer fails in Docker mounts because of Git dubious ownership / exit 128.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
