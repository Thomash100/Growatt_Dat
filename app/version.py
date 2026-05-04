VERSION = "0.001.8"
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
                    "Update-Badge in der Navigation wird aktiv ausgeblendet, wenn keine neue Version verfuegbar ist.",
                    "Badge bekommt einen klaren sichtbaren oder versteckten Zustand nach der Versionspruefung.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Release-Hinweis und Update-Seite bleiben unveraendert; nur der kurze Navigationshinweis reagiert genauer.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Alter neu-Hinweis kann nach einem Update-Check ohne neue Version nicht mehr sichtbar bleiben.",
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
                    "The update badge in the navigation is actively hidden when no newer version is available.",
                    "The badge gets a clear visible or hidden state after the version check.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Release notice and update page stay unchanged; only the short navigation hint reacts more precisely.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "A stale new badge can no longer remain visible after an update check without a newer version.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
