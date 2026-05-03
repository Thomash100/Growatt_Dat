# Architektur

`growatt-local-gateway` ist als lokaler Dienst für einen Raspberry Pi vorbereitet. Version 1 nutzt ausschließlich Mock-Daten und führt keine echte Growatt-Kommunikation aus.

## Hauptmodule

- `app.growatt`: Abstrakte Geräteschnittstelle, Mock-Gerät und Platzhalter für Listener, Decoder und Command-Client.
- `app.control`: Zero-Export-Regler und Safety-Prüfungen.
- `app.storage`: SQLite-Store für Messwerte, Entscheidungen, Einstellungen und Logs.
- `app.mqtt`: MQTT-Publisher und Home-Assistant-Auto-Discovery.
- `app.web`: FastAPI-Routen, Jinja2-Templates, statische Dateien und WebSocket-Livedaten.

## Datenfluss

1. Das Mock-Gerät erzeugt zyklisch Messwerte.
2. Die Messwerte werden in SQLite gespeichert.
3. Der Zero-Export-Regler berechnet eine Ziel-Ausgangsleistung.
4. Safety-Prüfungen verhindern unsichere Erhöhungen und begrenzen den Zielwert.
5. Die Entscheidung wird gespeichert und als Mock-Stellbefehl an das Mock-Gerät übergeben.
6. Messwerte, Entscheidungen, Einstellungen und Status werden per MQTT veröffentlicht.
7. Weboberfläche und WebSocket zeigen den aktuellen Zustand lokal an.

## Erweiterungspunkte

- `listener.py`: Lokaler Growatt-Listener für spätere TCP/UDP-Pakete.
- `decoder.py`: Umwandlung echter Growatt-Rohdaten in `Measurement`.
- `command.py`: Gekapselte, verifizierte Steuerbefehle.
- `GrowattDevice`: Gemeinsames Interface für Mock, lokalen Decoder, Datenlogger-Proxy oder Cloud-Forwarder.

