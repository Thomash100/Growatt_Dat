# Installation über GitHub

## Voraussetzungen auf Raspberry Pi installieren

```bash
sudo apt update
sudo apt install -y git docker.io docker-compose-plugin
sudo systemctl enable docker
sudo systemctl start docker
```

## Repository klonen

```bash
git clone https://github.com/Thomash100/Growatt_Dat.git growatt-local-gateway
cd growatt-local-gateway
```

## Konfiguration erstellen

```bash
cp .env.example .env
nano .env
```

Trage dort MQTT-Broker, Ports, Sprache (`UI_LANGUAGE=de` oder `UI_LANGUAGE=en`), lokale Messgeraete-Konfiguration und Regelparameter ein. Es gehören keine echten Zugangsdaten in das Repository.

Shelly 3EM Beispiel:

```env
METER_PROVIDER=shelly_3em
SHELLY_3EM_BASE_URL=http://192.168.1.100
SHELLY_3EM_GENERATION=auto
METER_POWER_SIGN=normal
```

## Dienst starten

```bash
docker compose up -d --build
```

## Logs anzeigen

```bash
docker compose logs -f
```

## Dienst stoppen

```bash
docker compose down
```

## Weboberfläche

```text
http://raspberrypi.local:8080
```

## Erstmaliger Push zu GitHub

Wenn der Projektordner noch kein Git-Repository ist:

```bash
git init
git add .
git commit -m "Initial Growatt local gateway mock version"
git branch -M main
git remote add origin https://github.com/Thomash100/Growatt_Dat.git
git push -u origin main
```

Wenn bereits ein Git-Repository existiert, bestehende Git-Einstellungen nicht überschreiben. Prüfe zuerst:

```bash
git status
git remote -v
```

Falls bereits ein Remote gesetzt ist, passe nur den notwendigen Teil gezielt an.
