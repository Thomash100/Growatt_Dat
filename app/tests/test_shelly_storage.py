from app.models import ShellyDeviceConfig, ShellyDeviceReading, utc_now
from app.storage.sqlite_store import SQLiteStore


def test_sqlite_store_persists_shelly_device_and_latest_reading():
    store = SQLiteStore(":memory:")
    store.init_db()
    device = store.save_shelly_device(
        ShellyDeviceConfig.from_mapping(
            {
                "id": "pv-shelly",
                "name": "PV Anlage",
                "base_url": "http://192.168.178.50",
                "generation": "gen2",
                "model": "SNPM-001PCEU16",
                "role": "pv",
            }
        )
    )

    store.save_shelly_reading(
        ShellyDeviceReading(
            timestamp=utc_now(),
            device_id=device.id,
            name=device.name,
            role=device.role,
            base_url=device.base_url,
            generation=device.generation,
            model=device.model,
            status="online",
            power_w=320.5,
            raw_values={"switch:0.apower": 320.5},
        )
    )

    devices = store.list_shelly_devices()
    latest = store.get_latest_shelly_readings()

    assert devices[0].name == "PV Anlage"
    assert devices[0].role == "pv"
    assert latest["pv-shelly"].power_w == 320.5
    assert latest["pv-shelly"].raw_values["switch:0.apower"] == 320.5


def test_shelly_device_rejects_invalid_role():
    try:
        ShellyDeviceConfig.from_mapping(
            {
                "id": "bad",
                "name": "Bad",
                "base_url": "http://192.168.178.51",
                "role": "coffee",
            }
        )
    except ValueError as exc:
        assert "role" in str(exc)
    else:
        raise AssertionError("Expected invalid role to raise")
