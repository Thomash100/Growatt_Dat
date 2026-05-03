VERSION = "0.001.4"
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
                    "Neue Update-Seite in der Weboberflaeche mit GitHub-Versionspruefung.",
                    "API-Endpunkt /api/update/check meldet aktuelle und verfuegbare Version.",
                    "Navigations-Badge zeigt an, wenn eine neuere GitHub-Version verfuegbar ist.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "README und Update-Dokumentation erklaeren Raspberry-Pi-Updates ueber GitHub.",
                    "Update-Check ist per .env konfigurierbar und kann deaktiviert werden.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Release-Notizen verwenden robuste ASCII-Symbole fuer saubere Anzeige.",
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
                    "New web update page with GitHub version checks.",
                    "API endpoint /api/update/check reports current and available versions.",
                    "Navigation badge shows when a newer GitHub version is available.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "README and update docs explain Raspberry Pi updates through GitHub.",
                    "Update checks are configurable through .env and can be disabled.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Release notes now use robust ASCII symbols for clean rendering.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
