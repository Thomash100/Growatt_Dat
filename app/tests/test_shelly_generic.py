import asyncio
import json

import httpx

from app.meters.shelly_generic import ShellyGenericReader, parse_gen1_status, parse_gen2_status
from app.models import ShellyDeviceConfig


def shelly_device(**values):
    base = {
        "id": "pv-shelly",
        "name": "PV Anlage",
        "base_url": "http://192.168.178.50",
        "role": "pv",
    }
    base.update(values)
    return ShellyDeviceConfig.from_mapping(base)


def test_gen2_switch_status_extracts_common_power_values():
    reading = parse_gen2_status(
        {
            "switch:0": {
                "output": True,
                "apower": 345.6,
                "voltage": 230.1,
                "current": 1.5,
                "aenergy": {"total": 12345.0},
                "temperature": {"tC": 42.5},
            }
        },
        shelly_device(model="SNPM-001PCEU16"),
        device_info={"model": "SNPM-001PCEU16"},
    )

    assert reading.power_w == 345.6
    assert reading.energy_wh == 12345.0
    assert reading.voltage_v == 230.1
    assert reading.current_a == 1.5
    assert reading.temperature_c == 42.5
    assert reading.relay_on is True
    assert reading.role == "pv"


def test_gen1_meter_status_sums_meter_power_and_can_invert_sign():
    reading = parse_gen1_status(
        {
            "meters": [
                {"power": 80.4, "total": 1000},
                {"power": 19.6, "total": 1200},
            ],
            "relays": [{"ison": True}],
        },
        shelly_device(generation="gen1", power_sign="inverted"),
        device_info={"type": "SHPLG-S"},
    )

    assert reading.power_w == -100.0
    assert reading.model == "SHPLG-S"
    assert reading.relay_on is True


def test_generic_reader_uses_gen2_shelly_get_status():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content.decode("utf-8"))
        if payload["method"] == "Shelly.GetDeviceInfo":
            return httpx.Response(200, json={"model": "SNSW-001P16EU"})
        if payload["method"] == "Shelly.GetStatus":
            return httpx.Response(200, json={"switch:0": {"apower": 55.5, "output": True}})
        return httpx.Response(404)

    reader = ShellyGenericReader(transport=httpx.MockTransport(handler))
    reading = asyncio.run(reader.read(shelly_device(generation="gen2")))

    assert reading.status == "online"
    assert reading.power_w == 55.5
    assert reading.model == "SNSW-001P16EU"
