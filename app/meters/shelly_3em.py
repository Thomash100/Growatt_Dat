from __future__ import annotations

from typing import Any

import httpx

from app.meters.device import EnergyMeter
from app.models import MeterReading, utc_now


class ShellyMeterError(RuntimeError):
    pass


class Shelly3EMMeter(EnergyMeter):
    def __init__(
        self,
        *,
        base_url: str,
        generation: str = "auto",
        timeout_seconds: float = 3.0,
        invert_sign: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.generation = generation
        self.timeout_seconds = timeout_seconds
        self.invert_sign = invert_sign

    async def get_latest_reading(self) -> MeterReading:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            if self.generation in {"auto", "gen2"}:
                try:
                    response = await client.post(
                        f"{self.base_url}/rpc",
                        json={"id": 1, "method": "EM.GetStatus", "params": {"id": 0}},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
                        payload = payload["result"]
                    return self.parse_gen2_status(payload, invert_sign=self.invert_sign)
                except Exception as exc:
                    if self.generation == "gen2":
                        raise ShellyMeterError(f"Shelly Gen2 EM.GetStatus failed: {exc}") from exc

            if self.generation in {"auto", "gen1"}:
                try:
                    response = await client.get(f"{self.base_url}/status")
                    response.raise_for_status()
                    return self.parse_gen1_status(response.json(), invert_sign=self.invert_sign)
                except Exception as exc:
                    raise ShellyMeterError(f"Shelly Gen1 /status failed: {exc}") from exc

        raise ShellyMeterError("Unsupported Shelly generation")

    @staticmethod
    def parse_gen1_status(payload: dict[str, Any], *, invert_sign: bool = False) -> MeterReading:
        emeters = payload.get("emeters")
        if not isinstance(emeters, list) or not emeters:
            raise ShellyMeterError("Shelly Gen1 status does not contain emeters")

        phase_powers: dict[str, float] = {}
        total_power = payload.get("total_power")
        if total_power is None:
            total_power = 0.0
            for index, emeter in enumerate(emeters):
                if not isinstance(emeter, dict):
                    raise ShellyMeterError("Shelly Gen1 emeter entry is invalid")
                if emeter.get("is_valid") is False:
                    raise ShellyMeterError(f"Shelly Gen1 emeter {index} is invalid")
                power = _as_float(emeter.get("power"), f"emeters[{index}].power")
                phase_powers[chr(ord("a") + index)] = power
                total_power += power
        else:
            total_power = _as_float(total_power, "total_power")
            for index, emeter in enumerate(emeters):
                if not isinstance(emeter, dict):
                    continue
                if emeter.get("is_valid") is False:
                    raise ShellyMeterError(f"Shelly Gen1 emeter {index} is invalid")
                power = emeter.get("power")
                if power is not None:
                    phase_powers[chr(ord("a") + index)] = _as_float(power, f"emeters[{index}].power")

        grid_power_w = int(round(total_power))
        if invert_sign:
            grid_power_w *= -1

        return MeterReading(
            timestamp=utc_now(),
            grid_power_w=grid_power_w,
            status="online",
            source="shelly_3em_gen1",
            phase_powers_w=phase_powers,
        )

    @staticmethod
    def parse_gen2_status(payload: dict[str, Any], *, invert_sign: bool = False) -> MeterReading:
        data = payload.get("params") if isinstance(payload.get("params"), dict) else payload
        total_power = data.get("total_act_power")
        if total_power is None:
            phase_values = [
                _as_float(data.get("a_act_power"), "a_act_power"),
                _as_float(data.get("b_act_power"), "b_act_power"),
                _as_float(data.get("c_act_power"), "c_act_power"),
            ]
            total_power = sum(phase_values)
        else:
            total_power = _as_float(total_power, "total_act_power")

        errors = data.get("errors") or []
        if errors:
            raise ShellyMeterError(f"Shelly Gen2 reports errors: {errors}")

        phase_powers = {}
        for phase in ("a", "b", "c"):
            value = data.get(f"{phase}_act_power")
            if value is not None:
                phase_powers[phase] = _as_float(value, f"{phase}_act_power")

        grid_power_w = int(round(total_power))
        if invert_sign:
            grid_power_w *= -1

        return MeterReading(
            timestamp=utc_now(),
            grid_power_w=grid_power_w,
            status="online",
            source="shelly_3em_gen2",
            phase_powers_w=phase_powers,
        )


def _as_float(value: Any, field_name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ShellyMeterError(f"Invalid Shelly value for {field_name}: {value!r}") from exc
