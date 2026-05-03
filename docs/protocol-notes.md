# Protocol Notes

Version 1 implementiert keine echte Growatt-Protokolldekodierung.

Diese Datei ist als Arbeitsnotiz für spätere Integrationen gedacht:

- Growatt NEO/NOAH-Frames sollen zuerst passiv geloggt und analysiert werden.
- Rohdaten dürfen nicht direkt aus der Weboberfläche an reale Geräte gesendet werden.
- Jede spätere Steuerfunktion muss durch `app.control.safety` laufen.
- Ein Cloud-Forwarder oder Datenlogger-Proxy soll als eigener Adapter hinter `GrowattDevice` umgesetzt werden.
- Sensible Zugangsdaten gehören ausschließlich in `.env` oder sichere Secret-Stores.

