VERSION = "0.001.7"
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
                    "Optionaler Web-Update-Installationsbutton mit lokalem Token-Schutz.",
                    "Neue API-Endpunkte fuer Web-Update-Status und Start.",
                    "Web-Update fuehrt kontrolliert git fetch, git pull und optional docker compose aus.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Web-Update ist standardmaessig deaktiviert und muss per .env freigeschaltet werden.",
                    "Dockerfile enthaelt git fuer optionale Update-Pruefungen im Container.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Token wird nicht im Frontend gespeichert und nach dem Start aus dem Eingabefeld entfernt.",
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
                    "Optional web update install button with local token protection.",
                    "New API endpoints for web update status and start.",
                    "Web update runs controlled git fetch, git pull, and optional docker compose steps.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Web update is disabled by default and must be enabled through .env.",
                    "Dockerfile includes git for optional update checks in the container.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Token is not stored in the frontend and is cleared from the input field after start.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
