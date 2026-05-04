VERSION = "0.001.9"
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
                    "Zusatz-Shellys koennen als lokale Datenquellen fuer PV, Verbraucher, Batterie oder Sonstiges angelegt werden.",
                    "Generischer Shelly-Leser fuer Gen1/Gen2 liest Leistung, Energie, Spannung, Strom, Temperatur und Relaisstatus, soweit das Modell diese Werte bereitstellt.",
                    "Integrations-Scan kann gefundene Shellys jetzt auch als Zusatz-Shelly uebernehmen.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Dashboard, WebSocket und MQTT-State enthalten eine Shelly-Zusammenfassung inklusive lokaler PV-Leistung.",
                    "SQLite speichert konfigurierte Zusatz-Shellys und deren letzte Messwerte.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Nicht-3EM-Shellys sind nicht mehr nur als nicht direkt uebernehmbar sichtbar, sondern koennen als Datenquelle genutzt werden.",
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
                    "Additional Shellys can be configured as local data sources for PV, loads, battery, or other readings.",
                    "A generic Gen1/Gen2 Shelly reader collects power, energy, voltage, current, temperature, and relay status when the model exposes those values.",
                    "The integration scan can now add discovered Shellys as additional Shelly sources.",
                ],
            },
            {
                "title": "Other Changes",
                "icon": "-",
                "changes": [
                    "Dashboard, WebSocket, and MQTT state include a Shelly summary with local PV power.",
                    "SQLite stores configured additional Shellys and their latest readings.",
                ],
            },
            {
                "title": "Bug Fixes",
                "icon": "+",
                "changes": [
                    "Non-3EM Shellys are no longer only shown as not directly applicable; they can be used as data sources.",
                ],
            },
        ],
    },
}


def release_notes_for(language: str) -> dict[str, object]:
    return RELEASE_NOTES.get(language, RELEASE_NOTES["de"])
