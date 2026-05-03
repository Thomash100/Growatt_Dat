# growatt-local-gateway

Lokaler Growatt-Energy-Gateway-Dienst für einen Raspberry Pi. Das Projekt soll später Growatt NEO/NOAH-Daten lokal empfangen, zwischenspeichern, für eine eigene Zero-Export-/Nulleinspeisungsregelung auswerten, per MQTT an Home Assistant weitergeben und eine lokale Weboberfläche mit Live-Grafiken bereitstellen.

## Status: frühe Entwicklungs-/Mock-Version

Aktuelle Version: `V0.001.4`

Version 1 implementiert noch keine echte Growatt-Protokolldekodierung, keine Growatt-Cloud-Anbindung und keine realen Steuerbefehle an echte Geräte. Alle Messwerte kommen aus einer Mock-Datenquelle.

## Funktionsumfang Version 1

- FastAPI-Webserver mit Dashboard, Live-Grafiken, Einstellungen und Logs.
- Zweisprachige Weboberfläche mit Deutsch/Englisch-Auswahl.
- WebSocket unter `/ws/live` für Live-Daten.
- SQLite-Speicherung für Messwerte, Regelentscheidungen, Einstellungen und Logs.
- Mock-Growatt-Gerät mit realistischen Schwankungen.
- Abstraktes `GrowattDevice`-Interface für spätere Adapter.
- Offene lokale Messgeräte-Schnittstelle mit Mock-Meter und Shelly-3EM-Adapter.
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
- `/settings`
- `/logs`
- `/update`
- `/api/status`
- `/api/update/check`
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

Payloads sind JSON.

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

## Update

Die normale Raspberry-Pi-Aktualisierung ueber `apt update` und `apt upgrade` aktualisiert Systempakete. Dieses GitHub-Projekt wird damit erst automatisch aktualisiert, wenn spaeter ein eigenes Debian-Paket oder ein APT-Repository bereitgestellt wird.

Die Weboberflaeche bietet unter `/update` eine Versionspruefung gegen GitHub. Die Installation erfolgt in dieser Version bewusst ueber die Konsole, weil die Weboberflaeche noch keine Anmeldung hat und ein Button fuer Host-Befehle im Heimnetz sicherheitskritisch waere.

```bash
cd growatt-local-gateway
git pull
docker compose up -d --build
```

Optional:

```bash
docker image prune -f
```

## Sicherheitshinweise

- Keine echten Growatt-Zugangsdaten in den Code schreiben.
- Keine `.env` committen.
- Keine Passwörter im Frontend anzeigen.
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
