# Integrationen

## Lokaler Netzwerk-Scan

Die Weboberflaeche bietet unter `/integrations` einen lokalen Scan fuer bekannte Integrationen. In Version `V0.001.5` werden Shelly 3EM und Shelly Pro 3EM erkannt.

Der Scan ist bewusst begrenzt:

- nur private IPv4-Netze wie `192.168.178.0/24`
- maximal konfigurierbare Host-Anzahl
- kurze HTTP-Timeouts
- keine Zugangsdaten
- keine Schreibbefehle an gefundene Geraete

## Konfiguration

```env
INTEGRATION_SCAN_DEFAULT_CIDR=192.168.178.0/24
INTEGRATION_SCAN_TIMEOUT_SECONDS=0.6
INTEGRATION_SCAN_CONCURRENCY=32
INTEGRATION_SCAN_MAX_HOSTS=254
```

## Shelly-Erkennung

Shelly Gen1 wird ueber den REST-Endpunkt `/shelly` erkannt. Shelly Pro/Gen2 wird ueber RPC erkannt:

- `Shelly.GetDeviceInfo`
- `EM.GetStatus`

Wenn ein Shelly 3EM erkannt wird, kann er in der Weboberflaeche als Messgeraet uebernommen werden. Dabei werden die lokalen Einstellungen aktualisiert und ohne Container-Neustart wirksam.

## Duplikate

Wenn dasselbe Shelly-Geraet ueber mehrere IP-Adressen gefunden wird, markiert der Scanner spaetere Treffer als Duplikat. Die erste numerisch sortierte IP-Adresse bleibt uebernehmbar, weitere Treffer zeigen `Duplikat von ...` und bieten keine zweite Uebernahme-Aktion an.
