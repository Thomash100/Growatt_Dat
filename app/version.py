VERSION = "0.001.3"
VERSION_LABEL = f"V{VERSION}"
RELEASE_CHANNEL = "stable"
PROJECT_WEBSITE = "https://github.com/Thomash100/Growatt_Dat"

RELEASE_NOTES = {
    "de": {
        "title": "Neue Version verfuegbar",
        "next_release_title": "Was ist neu in dieser Version",
        "changelog_title": "Changelog",
        "groups": [
            {
                "title": "New Features",
                "icon": "💫",
                "changes": [
                    "Versionsdialog im klaren Release-Layout mit Version, Release-Kanal und Website.",
                    "Aenderungsliste ist nach Kategorien gruppiert.",
                    "Versions-Badge bleibt in der Navigation sichtbar.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "☀️",
                "changes": [
                    "Release-Hinweis wird pro Browser und Version nur einmal angezeigt.",
                    "Release-Daten liegen zentral in app/version.py.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "🐞",
                "changes": [
                    "Keine neuen Fehlerbehebungen in dieser Version.",
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
                "icon": "💫",
                "changes": [
                    "Version dialog now uses a clear release layout with version, release channel, and website.",
                    "Changes are grouped by category.",
                    "The version badge remains visible in the navigation.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "☀️",
                "changes": [
                    "The release notice is shown only once per browser and version.",
                    "Release data is centralized in app/version.py.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "🐞",
                "changes": [
                    "No new bug fixes in this version.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
