# growatt-local-gateway

Lokaler Growatt-Energy-Gateway-Dienst für einen Raspberry Pi. Das Projekt soll später Growatt NEO/NOAH-Daten lokal empfangen, zwischenspeichern, für eine eigene Zero-Export-/Nulleinspeisungsregelung auswerten, per MQTT an Home Assistant weitergeben und eine lokale Weboberfläche mit Live-Grafiken bereitstellen.

## Status: frühe Entwicklungs-/Mock-Version

Aktuelle Version: `V0.001.10`

Version 1 implementiert noch keine echte Growatt-Protokolldekodierung, keine Growatt-Cloud-Anbindung und keine realen Steuerbefehle an echte Geräte. Alle Messwerte kommen aus einer Mock-Datenquelle.

## Funktionsumfang Version 1

- FastAPI-Webserver mit Dashboard, Live-Grafiken, Einstellungen und Logs.
- Zweisprachige Weboberfläche mit Deutsch/Englisch-Auswahl.
- WebSocket unter `/ws/live` für Live-Daten.
- SQLite-Speicherung für Messwerte, Regelentscheidungen, Einstellungen und Logs.
- Mock-Growatt-Gerät mit realistischen Schwankungen.
- Abstraktes `GrowattDevice`-Interface für spätere Adapter.
- Offene lokale Messgeräte-Schnittstelle mit Mock-Meter und Shelly-3EM-Adapter.
- Integrationen-Seite mit lokalem Netzwerk-Scan fuer Shelly 3EM / Shelly Pro 3EM.
- Zusatz-Shellys als lokale Datenquellen fuer PV-Leistung, Verbraucher, Batterie oder sonstige Messwerte.
- Langzeit-Tagesstatistik fuer PV-Ertrag, Netzbezug, Einspeisung, Batterie und Shelly-Daten.
- Zero-Export-Regelalgorithmus mit Safety-Checks und Fail-Safe.
- MQTT-Publisher für Home Assistant und Mosquitto.
- MQTT Auto Discovery unter `homeassistant/...`.
- Dockerfile, `docker-compose.yml`, `.env.example`.
- GitHub Actions Workflow für Tests.
- Update-Seite unter `/update` mit GitHub-Versionspruefung.

## Voraussetzungen

- Raspberry Pi oder Linux-System mit Docker.
- Git.
- MQTT-Broker, z. B. Mosquitto.
- Optional Home Assistant mit aktiviertem MQTT.

## Installation über GitHub

Voraussetzungen auf Raspberry Pi installieren:

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

Repository klonen:

```bash
git clone https://github.com/Thomash100/Growatt_Dat.git growatt-local-gateway
cd growatt-local-gateway
```

## Konfiguration über .env

```bash
cp .env.example .env
nano .env
```

Wichtige Variablen:

- `MQTT_HOST`
- `MQTT_PORT`
- `MQTT_USERNAME`
- `MQTT_PASSWORD`
- `MQTT_TOPIC_PREFIX`
- `MQTT_DISCOVERY_PREFIX`
- `DATABASE_PATH`
- `WEB_PORT`
- `UI_LANGUAGE` (`de` oder `en`)
- `METER_PROVIDER` (`mock` oder `shelly_3em`)
- `METER_POWER_SIGN` (`normal` oder `inverted`)
- `SHELLY_3EM_BASE_URL` (z. B. `http://192.168.178.252`)
- `SHELLY_3EM_GENERATION` (`auto`, `gen1` oder `gen2`)
- `SHELLY_3EM_TIMEOUT_SECONDS`
- `UPDATE_CHECK_ENABLED`
- `UPDATE_REPOSITORY`
- `UPDATE_CHECK_TIMEOUT_SECONDS`
- `WEB_UPDATE_ENABLED`
- `WEB_UPDATE_TOKEN`
- `WEB_UPDATE_TOKEN_REQUIRED`
- `WEB_UPDATE_WORKDIR`
- `WEB_UPDATE_COMMAND_TIMEOUT_SECONDS`
- `WEB_UPDATE_REQUIRE_CLEAN_TREE`
- `WEB_UPDATE_RUN_DOCKER_COMPOSE`
- `WEB_UPDATE_RESTART_AFTER_SUCCESS`
- `INTEGRATION_SCAN_DEFAULT_CIDR`
- `INTEGRATION_SCAN_TIMEOUT_SECONDS`
- `INTEGRATION_SCAN_CONCURRENCY`
- `INTEGRATION_SCAN_MAX_HOSTS`
- `ZERO_EXPORT_ENABLED`
- `TARGET_GRID_POWER_W`
- `GRID_POWER_BAND_MIN_W`
- `GRID_POWER_BAND_MAX_W`
- `CONTROL_INTERVAL_SECONDS`
- `MIN_OUTPUT_CHANGE_W`
- `OUTPUT_STEP_W`
- `MAX_OUTPUT_POWER_W`
- `MIN_OUTPUT_POWER_W`
- `MIN_SOC_PERCENT`
- `STALE_MEASUREMENT_SECONDS`

`.env` darf nicht committed werden. `.env.example` enthält nur Beispielwerte.

## Start mit Docker Compose

```bash
docker compose up -d --build
```

Logs anzeigen:

```bash
docker compose logs -f
```

Dienst stoppen:

```bash
docker compose down
```

## Weboberfläche

```text
http://raspberrypi.local:8080
```

Die Sprache der Weboberfläche ist über `UI_LANGUAGE=de` oder `UI_LANGUAGE=en` vorkonfigurierbar und kann später unter `/settings` ohne Container-Neustart geändert werden.

Lokale Endpunkte:

- `/`
- `/live`
- `/statistics`
- `/settings`
- `/integrations`
- `/logs`
- `/update`
- `/api/status`
- `/api/update/check`
- `/api/update/install/status`
- `/api/update/install`
- `/api/integrations/scan`
- `/api/integrations/apply`
- `/api/shelly-devices`
- `/api/statistics/daily`
- `/api/settings`
- `/api/meters`
- `/api/meter/latest`
- `/api/measurements/latest`
- `/api/measurements/history`
- `/api/control/latest`

## MQTT-Topics

Topic-Prefix: `growatt_local_gateway`

- `growatt_local_gateway/state`
- `growatt_local_gateway/measurements`
- `growatt_local_gateway/control`
- `growatt_local_gateway/status`
- `growatt_local_gateway/settings`
- `growatt_local_gateway/shelly`
- `growatt_local_gateway/statistics`

Payloads sind JSON.

## Langzeitdaten

Rohmesswerte bleiben in SQLite erhalten. Zusaetzlich schreibt der Dienst eine Tagesstatistik in die Tabelle `daily_energy`. Daraus entstehen lokale Langzeitwerte fuer PV-Ertrag, Ausgangsenergie, Netzbezug, Einspeisung, Batterie-Laden/-Entladen sowie Shelly-PV und weitere Shelly-Rollen.

Die Werte sind unter `/statistics` sichtbar und per API unter `/api/statistics/daily` abrufbar. Fuer Home Assistant wird der aktuelle Tagesstand auch unter `growatt_local_gateway/statistics` veroeffentlicht.

## Lokale Messgeräte

Der Regler nutzt den lokalen Grid-Meter-Wert als `grid_power_w`. Standard ist `METER_PROVIDER=mock`. Für einen Shelly 3EM:

```env
METER_PROVIDER=shelly_3em
SHELLY_3EM_BASE_URL=http://192.168.178.252
SHELLY_3EM_GENERATION=gen2
METER_POWER_SIGN=normal
```

Diese Werte sind Startwerte aus `.env`; danach kannst du Messgeraet-Typ, Shelly-Adresse, Generation, Timeout und Stromrichtung auf `/settings` aendern. Die Aenderungen werden in SQLite gespeichert und ohne Container-Neustart wirksam. Dein Shelly unter `192.168.178.252` antwortet als Shelly Pro/Gen2 per RPC, daher ist `SHELLY_3EM_GENERATION=gen2` passend.

Wenn die Stromrichtung deiner Wandler invertiert ist, setze `METER_POWER_SIGN=inverted` oder waehle auf der Website `Invertiert`. Shelly 3EM Gen1 wird über `/status` gelesen, Shelly Pro/Gen2 über `EM.GetStatus`; bei `auto` versucht der Adapter beides. Bei Meter-Fehlern setzt der Regler keine Leistungserhöhung.

Zusaetzliche Shellys koennen unter `/integrations` als lokale Datenquellen angelegt werden. Rollen sind `PV-Anlage`, `Verbraucher`, `Batterie` und `Sonstige`. Die App liest Gen1 und Gen2 allgemein aus und speichert verfuegbare Werte wie Leistung, Energie, Spannung, Strom, Temperatur, Relaisstatus und kompakte Rohdaten. Die PV-Summe erscheint im Dashboard als Shelly PV-Leistung und im MQTT-Topic `growatt_local_gateway/shelly`.

## Integrationen und Netzwerk-Scan

Unter `/integrations` kann ein lokaler Scan im privaten Heimnetz gestartet werden, z. B. `192.168.178.0/24`. Der Scanner nutzt kurze HTTP-Abfragen fuer bekannte Integrationen und ist auf private IPv4-Netze begrenzt. Gefundene Shelly 3EM / Shelly Pro 3EM Geraete koennen direkt als Netz-Messgeraet uebernommen werden. Andere Shellys koennen als Zusatz-Shelly fuer lokale Daten uebernommen werden.

Konfigurierbare Scan-Werte:

```env
INTEGRATION_SCAN_DEFAULT_CIDR=192.168.178.0/24
INTEGRATION_SCAN_TIMEOUT_SECONDS=0.6
INTEGRATION_SCAN_CONCURRENCY=32
INTEGRATION_SCAN_MAX_HOSTS=254
```

## Home-Assistant-Integration

Trage in `.env` den Mosquitto- oder Home-Assistant-MQTT-Broker ein. Danach veröffentlicht der Dienst Messwerte und Regelstatus unter dem konfigurierten Topic-Prefix.

## MQTT Auto Discovery

Discovery-Topics werden unter `homeassistant/...` veröffentlicht. Enthalten sind:

- PV-Leistung
- Ausgangsleistung
- Netzleistung
- Batterie-SOC
- Lade-/Entladeleistung
- Ziel-Ausgangsleistung
- Zero Export aktiv
- Gerätestatus
- letzter Stellbefehl
- letzter Fehler
- Shelly PV-Leistung
- Shelly Gesamtleistung

## Update

Die normale Raspberry-Pi-Aktualisierung ueber `apt update` und `apt upgrade` aktualisiert Systempakete. Dieses GitHub-Projekt wird damit erst automatisch aktualisiert, wenn spaeter ein eigenes Debian-Paket oder ein APT-Repository bereitgestellt wird.

Die Weboberflaeche bietet unter `/update` eine Versionspruefung gegen GitHub. Zusaetzlich gibt es einen optionalen Web-Update-Installationsbutton. Er ist standardmaessig deaktiviert und startet nur mit lokalem Token aus `.env`.

```bash
cd growatt-local-gateway
git pull
docker compose up -d --build
```

Optionaler Web-Update-Button:

```bash
openssl rand -hex 24
```

```env
WEB_UPDATE_ENABLED=true
WEB_UPDATE_TOKEN=bitte-ein-langes-zufaelliges-token-setzen
WEB_UPDATE_TOKEN_REQUIRED=true
WEB_UPDATE_WORKDIR=/app
WEB_UPDATE_REQUIRE_CLEAN_TREE=true
WEB_UPDATE_RUN_DOCKER_COMPOSE=true
WEB_UPDATE_RESTART_AFTER_SUCCESS=false
```

Wenn dir der Token im reinen Heimnetz zu unpraktisch ist, kannst du ihn bewusst deaktivieren:

```env
WEB_UPDATE_ENABLED=true
WEB_UPDATE_TOKEN_REQUIRED=false
WEB_UPDATE_TOKEN=
```

Dann blendet die Weboberflaeche das Tokenfeld aus und der Installationsbutton startet direkt. Das sollte nur im eigenen lokalen Netzwerk genutzt werden.

In Docker-Setups ist fuer echte Selbst-Updates zusaetzliche Vorbereitung noetig. Ohne Docker-Zugriff im Container zeigt die Weboberflaeche den Button als nicht bereit an. Fuer einen einfachen Git-Pull-Modus mit Neustart kann das optionale Override genutzt werden:

```bash
docker compose -f docker-compose.yml -f docker-compose.web-update.yml up -d --build
```

Optional:

```bash
docker image prune -f
```

## Sicherheitshinweise

- Keine echten Growatt-Zugangsdaten in den Code schreiben.
- Keine `.env` committen.
- Keine Passwörter im Frontend anzeigen.
- Web-Update nur mit langem lokalem Token aktivieren und nicht ins Internet freigeben.
- Version 1 sendet keine realen Steuerbefehle an echte Geräte.
- Spätere Hardwarebefehle müssen durch Safety-Prüfungen und klare Grenzwerte abgesichert werden.

## Fail-Safe-Konzept

Der Regler erlaubt keine Leistungserhöhung bei ungültigen oder veralteten Messwerten, zu niedrigem SOC, unbekanntem Gerätestatus oder Fehlerstatus. Zielwerte werden immer auf die konfigurierten Mindest- und Maximalwerte begrenzt. Bei veralteten Messwerten und SOC-Unterschreitung wird die Ausgangsleistung reduziert.

## Roadmap für echte Growatt-Integration

- Passiver lokaler Growatt-Listener für NEO/NOAH-Daten.
- Decoder für lokale Growatt-Frames.
- Datenlogger-Proxy oder GroBro-ähnliche Logik als Adapter.
- Optionaler Forwarder zur Growatt Cloud.
- Gekapselter Command-Client für verifizierte lokale Stellbefehle.
- Erweiterte Tests mit aufgezeichneten Protokollframes.
- Weitere lokale Messgeräte-Adapter hinter `EnergyMeter`, z. B. Tasmota, Modbus, MQTT-Meter oder Home-Assistant-Sensoren.
