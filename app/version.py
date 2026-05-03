VERSION = "0.001.6"
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
                    "Integrationsliste erkennt doppelte Shelly-Eintraege anhand der Geraete-ID.",
                    "Shelly 3EM Aktion ist jetzt klar als Netz-Messgeraet-Uebernahme beschriftet.",
                    "Integrationen werden numerisch nach IP-Adresse sortiert.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Integrationsliste zeigt nun eine Status-Spalte.",
                    "Duplikate werden als Duplikat der ersten gefundenen IP angezeigt.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Doppelte Shelly-Pro-3EM-IP-Adressen bieten keine zweite Uebernahme-Aktion mehr an.",
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
                    "Integration list detects duplicate Shelly entries by device ID.",
                    "Shelly 3EM action is now clearly labeled as grid-meter apply.",
                    "Integrations are sorted numerically by IP address.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Integration list now shows a status column.",
                    "Duplicates are shown as duplicates of the first discovered IP.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Duplicate Shelly Pro 3EM IP addresses no longer offer a second apply action.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
