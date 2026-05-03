# Update

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

