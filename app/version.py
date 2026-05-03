VERSION = "0.001.5"
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
                    "Neue Integrationen-Seite mit lokalem Netzwerk-Scan.",
                    "Shelly 3EM und Shelly Pro 3EM koennen automatisch erkannt werden.",
                    "Gefundene Shelly-3EM-Geraete koennen direkt als Messgeraet uebernommen werden.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Scan-Bereich, Timeout, Parallelitaet und Host-Limit sind per .env konfigurierbar.",
                    "Navigation um Integrationen erweitert.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Netzwerk-Scan ist auf private IPv4-Heimnetze begrenzt.",
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
                    "New integrations page with local network scanning.",
                    "Shelly 3EM and Shelly Pro 3EM devices can be detected automatically.",
                    "Detected Shelly 3EM devices can be applied directly as grid meters.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Scan range, timeout, concurrency, and host limit are configurable through .env.",
                    "Navigation now includes integrations.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Network scanning is limited to private IPv4 home networks.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
