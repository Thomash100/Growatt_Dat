from __future__ import annotations

from typing import Any


DEVICE = {
    "identifiers": ["growatt_local_gateway"],
    "name": "Growatt Local Gateway",
    "manufacturer": "Local Gateway",
    "model": "Mock Gateway v1",
}


def build_discovery_payloads(
    *,
    topic_prefix: str = "growatt_local_gateway",
    discovery_prefix: str = "homeassistant",
) -> list[tuple[str, dict[str, Any]]]:
    topic_prefix = topic_prefix.strip("/")
    discovery_prefix = discovery_prefix.strip("/")

    sensors = [
        ("pv_power", "PV-Leistung", "measurements", "pv_power_w", "W", "power", "measurement"),
        ("output_power", "Ausgangsleistung", "measurements", "output_power_w", "W", "power", "measurement"),
        ("grid_power", "Netzleistung", "measurements", "grid_power_w", "W", "power", "measurement"),
        ("battery_soc", "Batterie-SOC", "measurements", "battery_soc", "%", "battery", "measurement"),
        (
            "charge_discharge_power",
            "Lade-/Entladeleistung",
            "measurements",
            "charge_discharge_power_w",
            "W",
            "power",
            "measurement",
        ),
        ("target_output_power", "Ziel-Ausgangsleistung", "control", "target_output_power_w", "W", "power", None),
        ("last_command", "Letzter Stellbefehl", "control", "reason", None, None, None),
        ("last_error", "Letzter Fehler", "control", "error_status", None, None, None),
        ("device_status", "Gerätestatus", "status", "device_status", None, None, None),
    ]

    payloads: list[tuple[str, dict[str, Any]]] = []
    for object_id, name, source, json_key, unit, device_class, state_class in sensors:
        payload: dict[str, Any] = {
            "name": name,
            "unique_id": f"growatt_local_gateway_{object_id}",
            "state_topic": f"{topic_prefix}/{source}",
            "value_template": f"{{{{ value_json.{json_key} }}}}",
            "device": DEVICE,
        }
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        if state_class:
            payload["state_class"] = state_class
        payloads.append((f"{discovery_prefix}/sensor/growatt_local_gateway/{object_id}/config", payload))

    zero_export_payload = {
        "name": "Zero Export aktiv",
        "unique_id": "growatt_local_gateway_zero_export_enabled",
        "state_topic": f"{topic_prefix}/settings",
        "value_template": "{{ 'ON' if value_json.zero_export_enabled else 'OFF' }}",
        "payload_on": "ON",
        "payload_off": "OFF",
        "device": DEVICE,
    }
    payloads.append(
        (
            f"{discovery_prefix}/binary_sensor/growatt_local_gateway/zero_export_enabled/config",
            zero_export_payload,
        )
    )

    return payloads

