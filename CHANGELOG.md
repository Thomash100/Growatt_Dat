# Changelog

## V0.001.8 - 2026-05-05

- Update-Badge `neu` wird nach der Versionspruefung aktiv ausgeblendet, wenn keine neue Version verfuegbar ist.
- Initialer Badge-Zustand ist jetzt auch fuer Screenreader eindeutig versteckt.
- Verhindert, dass ein alter Navigationshinweis nach einem Update-Check sichtbar haengen bleibt.

## V0.001.7 - 2026-05-03

- Optionalen Web-Update-Installationsbutton mit Token-Schutz ergaenzt.
- API-Endpunkte `/api/update/install/status` und `/api/update/install` ergaenzt.
- Kontrollierter Update-Runner fuer `git fetch`, `git pull --ff-only` und optional `docker compose up -d --build`.
- Web-Update ist standardmaessig deaktiviert und muss ueber `.env` aktiviert werden.

## V0.001.6 - 2026-05-03

- Integrationsliste sortiert IP-Adressen numerisch.
- Doppelte Shelly-Eintraege werden anhand der Geraete-ID markiert.
- Shelly-3EM-Uebernahme ist klarer als Netz-Messgeraet-Aktion beschriftet.
- Status-Spalte fuer Integrationskandidaten ergaenzt.

## V0.001.5 - 2026-05-03

- Integrationen-Seite `/integrations` mit lokalem Netzwerk-Scan ergaenzt.
- Shelly 3EM / Shelly Pro 3EM Erkennung fuer Gen1 REST und Gen2 RPC ergaenzt.
- Gefundene Shelly-3EM-Geraete koennen als Messgeraet uebernommen werden.
- Scan ist auf private IPv4-Netze begrenzt und per `.env` konfigurierbar.

## V0.001.4 - 2026-05-03

- Update-Seite `/update` mit GitHub-Versionspruefung ergaenzt.
- API-Endpunkt `/api/update/check` fuer aktuelle und verfuegbare Versionen ergaenzt.
- Navigationshinweis fuer verfuegbare Updates ergaenzt.
- README und Update-Dokumentation fuer Raspberry-Pi-/GitHub-Updates erweitert.

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
