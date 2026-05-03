# Architektur

`growatt-local-gateway` ist als lokaler Dienst fuer einen Raspberry Pi vorbereitet. Version 1 nutzt weiterhin Mock-Growatt-Daten und fuehrt keine echte Growatt-Kommunikation aus.

## Hauptmodule

- `app.growatt`: Abstrakte Geraeteschnittstelle, Mock-Geraet und Platzhalter fuer Listener, Decoder und Command-Client.
- `app.meters`: Offene lokale Messgeraete-Schnittstelle mit Mock-Meter und Shelly-3EM-Adapter.
- `app.control`: Zero-Export-Regler und Safety-Pruefungen.
- `app.storage`: SQLite-Store fuer Messwerte, Entscheidungen, Einstellungen und Logs.
- `app.mqtt`: MQTT-Publisher und Home-Assistant-Auto-Discovery.
- `app.web`: FastAPI-Routen, Jinja2-Templates, statische Dateien und WebSocket-Livedaten.

## Datenfluss

1. Das Mock-Growatt-Geraet erzeugt zyklisch Geraete- und Leistungswerte.
2. Der aktive lokale Grid-Meter liefert den Netzleistungswert.
3. Der Grid-Meter-Wert wird als `grid_power_w` in die Messung uebernommen.
4. Die Messwerte werden in SQLite gespeichert.
5. Der Zero-Export-Regler berechnet eine Ziel-Ausgangsleistung.
6. Safety-Pruefungen verhindern unsichere Erhoehungen und begrenzen den Zielwert.
7. Die Entscheidung wird gespeichert und als Mock-Stellbefehl an das Mock-Geraet uebergeben.
8. Messwerte, Entscheidungen, Einstellungen und Status werden per MQTT veroeffentlicht.
9. Weboberflaeche und WebSocket zeigen den aktuellen Zustand lokal an.

## Erweiterungspunkte

- `listener.py`: Lokaler Growatt-Listener fuer spaetere TCP/UDP-Pakete.
- `decoder.py`: Umwandlung echter Growatt-Rohdaten in `Measurement`.
- `command.py`: Gekapselte, verifizierte Steuerbefehle.
- `GrowattDevice`: Gemeinsames Interface fuer Mock, lokalen Decoder, Datenlogger-Proxy oder Cloud-Forwarder.
- `EnergyMeter`: Gemeinsames Interface fuer lokale Messgeraete wie Shelly 3EM, Tasmota, Modbus, MQTT-Meter oder Home-Assistant-Sensoren.
