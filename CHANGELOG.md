# Changelog

## V0.001.3 - 2026-05-03

- Release-Popup im klaren Versionslayout mit Version, Release-Kanal und Website umgesetzt.
- Changelog im Popup nach Kategorien gruppiert.
- Version bleibt als Badge in der Webnavigation sichtbar.

## V0.001.2 - 2026-05-03

- Versionsnummer in der Weboberfläche sichtbar gemacht.
- Einmaliges Update-Popup mit Änderungsliste ergänzt.
- Release-Hinweis wird pro Browser und Version gespeichert.

## V0.001.1 - 2026-05-03

- Lesbare Projektversion `V0.001.1` eingeführt.
- Version wird im FastAPI-Metadatenfeld und im Status-/WebSocket-Snapshot ausgegeben.
- GitHub-Actions-Testimport stabilisiert.
- Messgeräte-Parameter sind über die Weboberfläche konfigurierbar.
- Shelly Pro 3EM unter `192.168.178.252` als Gen2/RPC-Beispiel dokumentiert.

## 0.1.0 - 2026-05-03

- Initiale Mock-Version des lokalen Growatt-Gateway-Dienstes.
- FastAPI-Weboberfläche mit Dashboard, Live-Grafiken, Einstellungen und Logs.
- Mock-Datenquelle für PV, Ausgangsleistung, Netzleistung, SOC und Gerätestatus.
- Zero-Export-Regelalgorithmus mit Safety-Prüfungen und Fail-Safe-Verhalten.
- SQLite-Speicherung für Messwerte, Regelentscheidungen, Einstellungen und Logs.
- MQTT-Publisher und MQTT Auto Discovery für Home Assistant.
- Dockerfile, Docker Compose, GitHub Actions und Projektdokumentation.
