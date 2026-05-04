from __future__ import annotations

from typing import Any

import httpx

from app.models import ShellyDeviceConfig, ShellyDeviceReading, utc_now


class ShellyGenericError(RuntimeError):
    pass


class ShellyGenericReader:
    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self.transport = transport

    async def read(self, device: ShellyDeviceConfig) -> ShellyDeviceReading:
        timeout = httpx.Timeout(device.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, transport=self.transport) as client:
            if device.generation in {"auto", "gen2"}:
                try:
                    info = await post_rpc(client, device.base_url, "Shelly.GetDeviceInfo")
                    status = await post_rpc(client, device.base_url, "Shelly.GetStatus")
                    if isinstance(status, dict):
                        return parse_gen2_status(status, device, device_info=info if isinstance(info, dict) else None)
                except Exception as exc:
                    if device.generation == "gen2":
                        raise ShellyGenericError(f"Shelly Gen2 read failed: {exc}") from exc

            if device.generation in {"auto", "gen1"}:
                try:
                    info = await get_json(client, f"{device.base_url}/shelly")
                    status = await get_json(client, f"{device.base_url}/status")
                    if isinstance(status, dict):
                        return parse_gen1_status(status, device, device_info=info if isinstance(info, dict) else None)
                except Exception as exc:
                    raise ShellyGenericError(f"Shelly Gen1 read failed: {exc}") from exc

        raise ShellyGenericError("Shelly generation could not be detected")


async def post_rpc(
    client: httpx.AsyncClient,
    base_url: str,
    method: str,
    params: dict[str, Any] | None = None,
) -> Any:
    response = await client.post(
        f"{base_url.rstrip('/')}/rpc",
        json={"id": 1, "method": method, "params": params or {}},
    )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
        return payload["result"]
    return payload


async def get_json(client: httpx.AsyncClient, url: str) -> Any:
    response = await client.get(url)
    response.raise_for_status()
    return response.json()


def parse_gen2_status(
    payload: dict[str, Any],
    device: ShellyDeviceConfig,
    *,
    device_info: dict[str, Any] | None = None,
) -> ShellyDeviceReading:
    data = payload.get("params") if isinstance(payload.get("params"), dict) else payload
    if not isinstance(data, dict):
        raise ShellyGenericError("Shelly Gen2 status is not an object")
    errors = collect_errors(data)
    if errors:
        raise ShellyGenericError(f"Shelly Gen2 reports errors: {errors}")

    raw_values = compact_values({**({"device_info": device_info} if device_info else {}), "status": data})
    return ShellyDeviceReading(
        timestamp=utc_now(),
        device_id=device.id,
        name=device.name,
        role=device.role,
        base_url=device.base_url,
        generation="gen2",
        model=device.model or string_or_none((device_info or {}).get("model")),
        status="online",
        power_w=apply_power_sign(extract_power(data), device.power_sign),
        energy_wh=extract_energy(data),
        voltage_v=average_named_values(data, {"voltage", "a_voltage", "b_voltage", "c_voltage"}),
        current_a=sum_named_values(data, {"current", "a_current", "b_current", "c_current"}),
        temperature_c=first_named_value(data, {"tC", "temperature"}),
        relay_on=first_bool_value(data, {"output", "ison"}),
        raw_values=raw_values,
    )


def parse_gen1_status(
    payload: dict[str, Any],
    device: ShellyDeviceConfig,
    *,
    device_info: dict[str, Any] | None = None,
) -> ShellyDeviceReading:
    raw_values = compact_values({**({"device_info": device_info} if device_info else {}), "status": payload})
    return ShellyDeviceReading(
        timestamp=utc_now(),
        device_id=device.id,
        name=device.name,
        role=device.role,
        base_url=device.base_url,
        generation="gen1",
        model=device.model
        or string_or_none((device_info or {}).get("type"))
        or string_or_none((device_info or {}).get("model")),
        status="online",
        power_w=apply_power_sign(extract_power(payload), device.power_sign),
        energy_wh=extract_energy(payload),
        voltage_v=average_named_values(payload, {"voltage"}),
        current_a=sum_named_values(payload, {"current"}),
        temperature_c=first_named_value(payload, {"temperature", "tmp", "tC"}),
        relay_on=first_bool_value(payload, {"ison", "output"}),
        raw_values=raw_values,
    )


def extract_power(data: dict[str, Any]) -> float | None:
    total = first_named_value(data, {"total_act_power", "total_power"})
    if total is not None:
        return total

    powers: list[float] = []
    for value in nested_dicts(data):
        component_total = first_direct_number(value, {"total_act_power", "total_power"})
        if component_total is not None:
            powers.append(component_total)
            continue
        component_power = first_direct_number(value, {"apower", "act_power", "power"})
        if component_power is not None:
            powers.append(component_power)

    if powers:
        return round(sum(powers), 3)
    return first_named_value(data, {"apower", "act_power", "power"})


def extract_energy(data: dict[str, Any]) -> float | None:
    total = first_named_value(data, {"total_act_energy", "total_energy", "energy_wh"})
    if total is not None:
        return total
    for value in nested_dicts(data):
        if isinstance(value.get("aenergy"), dict):
            energy = first_direct_number(value["aenergy"], {"total", "by_minute"})
            if energy is not None:
                return energy
        energy = first_direct_number(value, {"energy", "total"})
        if energy is not None:
            return energy
    return None


def collect_errors(data: dict[str, Any]) -> list[Any]:
    errors: list[Any] = []
    for value in nested_dicts(data):
        current = value.get("errors")
        if current:
            errors.append(current)
    return errors


def compact_values(data: Any, *, limit: int = 120) -> dict[str, Any]:
    values: dict[str, Any] = {}

    def visit(value: Any, prefix: str) -> None:
        if len(values) >= limit:
            return
        if isinstance(value, dict):
            for key, item in value.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                visit(item, next_prefix)
            return
        if isinstance(value, list):
            for index, item in enumerate(value[:8]):
                visit(item, f"{prefix}.{index}")
            return
        if value is None or isinstance(value, bool | int | float):
            values[prefix] = value
        elif isinstance(value, str) and len(value) <= 160:
            values[prefix] = value

    visit(data, "")
    return values


def nested_dicts(data: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            items.append(value)
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(data)
    return items


def first_named_value(data: dict[str, Any], names: set[str]) -> float | None:
    for value in nested_dicts(data):
        number = first_direct_number(value, names)
        if number is not None:
            return number
    return None


def average_named_values(data: dict[str, Any], names: set[str]) -> float | None:
    values = [number for item in nested_dicts(data) for number in [first_direct_number(item, names)] if number is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 3)


def sum_named_values(data: dict[str, Any], names: set[str]) -> float | None:
    values = [number for item in nested_dicts(data) for number in [first_direct_number(item, names)] if number is not None]
    if not values:
        return None
    return round(sum(values), 3)


def first_direct_number(data: dict[str, Any], names: set[str]) -> float | None:
    for name in names:
        value = data.get(name)
        if value is None:
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return None


def first_bool_value(data: dict[str, Any], names: set[str]) -> bool | None:
    for value in nested_dicts(data):
        for name in names:
            current = value.get(name)
            if isinstance(current, bool):
                return current
    return None


def apply_power_sign(value: float | None, power_sign: str) -> float | None:
    if value is None:
        return None
    signed = value * -1 if power_sign == "inverted" else value
    return round(signed, 3)


def string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
