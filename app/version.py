VERSION = "0.001.2"
VERSION_LABEL = f"V{VERSION}"

RELEASE_NOTES = {
    "de": {
        "title": "Neue Version verfuegbar",
        "summary": "Aenderungen in dieser Version",
        "changes": [
            "Versionsnummer ist in der Weboberflaeche sichtbar.",
            "Nach einem Update erscheint einmalig ein Hinweisfenster mit Aenderungsliste.",
            "Der Hinweis wird im Browser gespeichert und pro Version nur einmal angezeigt.",
        ],
    },
    "en": {
        "title": "New version available",
        "summary": "Changes in this version",
        "changes": [
            "The version number is visible in the web interface.",
            "After an update, a one-time popup shows the change list.",
            "The notice is stored in the browser and shown only once per version.",
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
