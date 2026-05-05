# Update

## Update-Pruefung in der Weboberflaeche

Die Seite `/update` prueft ueber GitHub, ob eine neuere Version oder ein neuer Tag fuer `Thomash100/Growatt_Dat` verfuegbar ist. Die Pruefung kann ueber `.env` gesteuert werden:

```env
UPDATE_CHECK_ENABLED=true
UPDATE_REPOSITORY=Thomash100/Growatt_Dat
UPDATE_CHECK_TIMEOUT_SECONDS=4
```

Die normale Raspbian-Aktualisierung mit `apt update` und `apt upgrade` aktualisiert nur installierte Systempakete. Dieses Projekt wird dadurch erst automatisch aktualisiert, wenn spaeter ein eigenes Debian-Paket oder APT-Repository bereitsteht.

## Optionaler Web-Update-Button

Der Installationsbutton auf `/update` ist standardmaessig deaktiviert. Zum Aktivieren muss ein langes lokales Token in `.env` gesetzt werden:

```bash
openssl rand -hex 24
```

```env
WEB_UPDATE_ENABLED=true
WEB_UPDATE_TOKEN=bitte-ein-langes-zufaelliges-token-setzen
WEB_UPDATE_TOKEN_REQUIRED=true
WEB_UPDATE_WORKDIR=/app
WEB_UPDATE_COMMAND_TIMEOUT_SECONDS=600
WEB_UPDATE_REQUIRE_CLEAN_TREE=true
WEB_UPDATE_RUN_DOCKER_COMPOSE=true
WEB_UPDATE_RESTART_AFTER_SUCCESS=false
```

Wenn der Dienst ausschliesslich im eigenen Heimnetz erreichbar ist, kann der Token bewusst abgeschaltet werden:

```env
WEB_UPDATE_ENABLED=true
WEB_UPDATE_TOKEN_REQUIRED=false
WEB_UPDATE_TOKEN=
```

Dann zeigt die Weboberflaeche kein Tokenfeld und der Installationsbutton startet direkt. Diese Einstellung nicht fuer eine aus dem Internet erreichbare Installation verwenden.

Der Button fuehrt keine freie Shell-Eingabe aus. Der Ablauf ist fest verdrahtet:

```text
git status --porcelain
git fetch --tags origin
git pull --ff-only
docker compose up -d --build
```

Wenn `WEB_UPDATE_RUN_DOCKER_COMPOSE=false` gesetzt ist, wird nur der Git-Teil ausgefuehrt. Das ist fuer Docker-Setups mit Quellcode-Mount interessant:

```bash
docker compose -f docker-compose.yml -f docker-compose.web-update.yml up -d --build
```

Mit `WEB_UPDATE_RESTART_AFTER_SUCCESS=true` beendet sich die App nach erfolgreichem Git-Pull. Docker startet sie durch `restart: unless-stopped` wieder. Das ist einfacher als Docker-Socket-Zugriff im Container, aktualisiert aber keine Python-Abhaengigkeiten.

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
