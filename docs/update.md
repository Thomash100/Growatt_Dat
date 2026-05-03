# Update

## Update-Pruefung in der Weboberflaeche

Die Seite `/update` prueft ueber GitHub, ob eine neuere Version oder ein neuer Tag fuer `Thomash100/Growatt_Dat` verfuegbar ist. Die Pruefung kann ueber `.env` gesteuert werden:

```env
UPDATE_CHECK_ENABLED=true
UPDATE_REPOSITORY=Thomash100/Growatt_Dat
UPDATE_CHECK_TIMEOUT_SECONDS=4
```

Die normale Raspbian-Aktualisierung mit `apt update` und `apt upgrade` aktualisiert nur installierte Systempakete. Dieses Projekt wird dadurch erst automatisch aktualisiert, wenn spaeter ein eigenes Debian-Paket oder APT-Repository bereitsteht.

Ein Installieren-Button in der Weboberflaeche ist in dieser Version bewusst nicht aktiv, weil die Weboberflaeche noch keine Anmeldung besitzt und Host-Befehle wie `git pull` oder `docker compose up` im Heimnetz sicherheitskritisch waeren.

## Update installieren

Im Projektverzeichnis:

```bash
cd growatt-local-gateway
git pull
docker compose up -d --build
```

Optional alte Docker-Images bereinigen:

```bash
docker image prune -f
```

Die SQLite-Datenbank unter `./data` bleibt dabei erhalten.
