VERSION = "0.001.12"
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
                    "Globale CSS-Regel fuer das hidden-Attribut verhindert sichtbar bleibende versteckte Elemente.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Update-Badge nutzt weiterhin die GitHub-Versionspruefung, wird aber initial sicher per CSS versteckt.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Der neu-Hinweis kann nicht mehr durch display:inline-flex sichtbar bleiben, wenn hidden gesetzt ist.",
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
                    "A global CSS rule for the hidden attribute prevents hidden elements from staying visible.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "The update badge still uses the GitHub version check, but is now reliably hidden by CSS initially.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "The new hint can no longer stay visible through display:inline-flex while hidden is set.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
