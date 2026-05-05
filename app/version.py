VERSION = "0.001.10"
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
                    "Langzeit-Tagesstatistik fuer PV-Ertrag, Netzbezug, Einspeisung, Batterie und Shelly-Datenquellen.",
                    "Neue Langzeitseite unter /statistics und API unter /api/statistics/daily.",
                    "Web-Update kann im eigenen Heimnetz optional ohne Tokenfeld genutzt werden.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "MQTT veroeffentlicht aktuelle Tageswerte unter growatt_local_gateway/statistics.",
                    "Dokumentation fuer tokenfreies Web-Update und Langzeitdaten erweitert.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Update-Seite blendet das Tokenfeld aus, wenn WEB_UPDATE_TOKEN_REQUIRED=false gesetzt ist.",
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
                    "Long-term daily statistics for PV yield, grid import, grid export, battery, and Shelly data sources.",
                    "New long-term page at /statistics and API at /api/statistics/daily.",
                    "Web update can optionally be used without a token field on your own home network.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "MQTT publishes current daily values at growatt_local_gateway/statistics.",
                    "Documentation extended for token-free web updates and long-term data.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "The update page hides the token field when WEB_UPDATE_TOKEN_REQUIRED=false is set.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
