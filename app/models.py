from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def datetime_to_iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def datetime_from_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "y", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "n", "off", "disabled", ""}:
        return False
    raise ValueError(f"Invalid boolean value: {value!r}")


def parse_int(value: Any, field_name: str) -> int:
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid integer value for {field_name}: {value!r}") from exc


def parse_float(value: Any, field_name: str) -> float:
    try:
        parsed = float(str(value).strip())
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid float value for {field_name}: {value!r}") from exc
    if not isfinite(parsed):
        raise ValueError(f"Invalid float value for {field_name}: {value!r}")
    return parsed


SHELLY_DEVICE_ROLES = {"pv", "load", "battery", "other"}


@dataclass(slots=True)
class Measurement:
    timestamp: datetime
    pv_power_w: int
    output_power_w: int
    grid_power_w: int
    battery_soc: int
    charge_discharge_power_w: int
    device_status: str

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = datetime_to_iso(self.timestamp)
        return payload

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Measurement":
        return cls(
            timestamp=datetime_from_iso(row["timestamp"]),
            pv_power_w=int(row["pv_power_w"]),
            output_power_w=int(row["output_power_w"]),
            grid_power_w=int(row["grid_power_w"]),
            battery_soc=int(row["battery_soc"]),
            charge_discharge_power_w=int(row["charge_discharge_power_w"]),
            device_status=str(row["device_status"]),
        )


@dataclass(slots=True)
class MeterReading:
    timestamp: datetime
    grid_power_w: int
    status: str
    source: str
    phase_powers_w: dict[str, float]
    error_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = datetime_to_iso(self.timestamp)
        return payload


@dataclass(frozen=True, slots=True)
class ShellyDeviceConfig:
    id: str
    name: str
    base_url: str
    generation: str = "auto"
    model: str | None = None
    role: str = "pv"
    power_sign: str = "normal"
    enabled: bool = True
    timeout_seconds: float = 3.0
    unique_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["created_at"] = None if self.created_at is None else datetime_to_iso(self.created_at)
        payload["updated_at"] = None if self.updated_at is None else datetime_to_iso(self.updated_at)
        return payload

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, Any],
        base: "ShellyDeviceConfig | None" = None,
    ) -> "ShellyDeviceConfig":
        current = asdict(base or cls(id=str(uuid4()), name="", base_url=""))
        for field in fields(cls):
            if field.name not in values:
                continue
            raw_value = values[field.name]
            if field.name in {"enabled"}:
                current[field.name] = parse_bool(raw_value)
            elif field.name in {"timeout_seconds"}:
                current[field.name] = parse_float(raw_value, field.name)
            elif field.name in {"created_at", "updated_at"}:
                if isinstance(raw_value, datetime):
                    current[field.name] = raw_value
                else:
                    current[field.name] = None if raw_value in {None, ""} else datetime_from_iso(str(raw_value))
            elif field.name in {"model", "unique_id"}:
                text = "" if raw_value is None else str(raw_value).strip()
                current[field.name] = text or None
            elif field.name in {"generation", "role", "power_sign"}:
                current[field.name] = str(raw_value).strip().lower()
            else:
                current[field.name] = str(raw_value).strip()
        device = cls(**current)
        device.validate()
        return device

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "ShellyDeviceConfig":
        return cls.from_mapping(
            {
                "id": row["id"],
                "name": row["name"],
                "base_url": row["base_url"],
                "generation": row["generation"],
                "model": row["model"],
                "role": row["role"],
                "power_sign": row["power_sign"],
                "enabled": row["enabled"],
                "timeout_seconds": row["timeout_seconds"],
                "unique_id": row["unique_id"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def validate(self) -> None:
        if not self.id:
            raise ValueError("Shelly device id must not be empty")
        if not self.name:
            raise ValueError("Shelly device name must not be empty")
        if not self.base_url.startswith("http://"):
            raise ValueError("Shelly base_url must start with http://")
        if self.generation not in {"auto", "gen1", "gen2"}:
            raise ValueError("Shelly generation must be auto, gen1, or gen2")
        if self.role not in SHELLY_DEVICE_ROLES:
            raise ValueError("Shelly role must be pv, load, battery, or other")
        if self.power_sign not in {"normal", "inverted"}:
            raise ValueError("Shelly power_sign must be normal or inverted")
        if self.timeout_seconds <= 0:
            raise ValueError("Shelly timeout_seconds must be greater than 0")


@dataclass(slots=True)
class ShellyDeviceReading:
    timestamp: datetime
    device_id: str
    name: str
    role: str
    base_url: str
    generation: str
    model: str | None
    status: str
    power_w: float | None = None
    energy_wh: float | None = None
    voltage_v: float | None = None
    current_a: float | None = None
    temperature_c: float | None = None
    relay_on: bool | None = None
    raw_values: dict[str, Any] | None = None
    error_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = datetime_to_iso(self.timestamp)
        payload["raw_values"] = self.raw_values or {}
        return payload

    @classmethod
    def from_row(cls, row: Mapping[str, Any], raw_values: dict[str, Any] | None = None) -> "ShellyDeviceReading":
        return cls(
            timestamp=datetime_from_iso(row["timestamp"]),
            device_id=str(row["device_id"]),
            name=str(row["name"]),
            role=str(row["role"]),
            base_url=str(row["base_url"]),
            generation=str(row["generation"]),
            model=None if row["model"] is None else str(row["model"]),
            status=str(row["status"]),
            power_w=None if row["power_w"] is None else float(row["power_w"]),
            energy_wh=None if row["energy_wh"] is None else float(row["energy_wh"]),
            voltage_v=None if row["voltage_v"] is None else float(row["voltage_v"]),
            current_a=None if row["current_a"] is None else float(row["current_a"]),
            temperature_c=None if row["temperature_c"] is None else float(row["temperature_c"]),
            relay_on=None if row["relay_on"] is None else parse_bool(row["relay_on"]),
            raw_values=raw_values or {},
            error_status=row["error_status"],
        )


@dataclass(slots=True)
class DailyEnergySummary:
    date: str
    updated_at: datetime
    sample_count: int = 0
    pv_energy_wh: float = 0.0
    output_energy_wh: float = 0.0
    grid_import_wh: float = 0.0
    grid_export_wh: float = 0.0
    battery_charge_wh: float = 0.0
    battery_discharge_wh: float = 0.0
    shelly_pv_energy_wh: float = 0.0
    shelly_load_energy_wh: float = 0.0
    shelly_battery_charge_wh: float = 0.0
    shelly_battery_discharge_wh: float = 0.0
    shelly_other_energy_wh: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["updated_at"] = datetime_to_iso(self.updated_at)
        for key, value in list(payload.items()):
            if key.endswith("_wh"):
                payload[key] = round(float(value), 3)
                payload[key.replace("_wh", "_kwh")] = round(float(value) / 1000.0, 3)
        return payload

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "DailyEnergySummary":
        return cls(
            date=str(row["date"]),
            updated_at=datetime_from_iso(row["updated_at"]),
            sample_count=int(row["sample_count"]),
            pv_energy_wh=float(row["pv_energy_wh"]),
            output_energy_wh=float(row["output_energy_wh"]),
            grid_import_wh=float(row["grid_import_wh"]),
            grid_export_wh=float(row["grid_export_wh"]),
            battery_charge_wh=float(row["battery_charge_wh"]),
            battery_discharge_wh=float(row["battery_discharge_wh"]),
            shelly_pv_energy_wh=float(row["shelly_pv_energy_wh"]),
            shelly_load_energy_wh=float(row["shelly_load_energy_wh"]),
            shelly_battery_charge_wh=float(row["shelly_battery_charge_wh"]),
            shelly_battery_discharge_wh=float(row["shelly_battery_discharge_wh"]),
            shelly_other_energy_wh=float(row["shelly_other_energy_wh"]),
        )


@dataclass(frozen=True, slots=True)
class ControlSettings:
    ui_language: str = "de"
    meter_provider: str = "mock"
    meter_power_sign: str = "normal"
    shelly_3em_base_url: str = "http://192.168.178.252"
    shelly_3em_generation: str = "auto"
    shelly_3em_timeout_seconds: float = 3.0
    zero_export_enabled: bool = True
    target_grid_power_w: int = 30
    grid_power_band_min_w: int = 20
    grid_power_band_max_w: int = 80
    control_interval_seconds: int = 5
    min_output_change_w: int = 30
    output_step_w: int = 50
    max_output_power_w: int = 800
    min_output_power_w: int = 0
    min_soc_percent: int = 15
    stale_measurement_seconds: int = 10

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_mapping(
        cls,
        values: Mapping[str, Any],
        base: "ControlSettings | None" = None,
    ) -> "ControlSettings":
        current = (base or cls()).to_dict()
        bool_fields = {"zero_export_enabled"}
        lowercase_string_fields = {
            "ui_language",
            "meter_provider",
            "meter_power_sign",
            "shelly_3em_generation",
        }
        float_fields = {"shelly_3em_timeout_seconds"}
        for field in fields(cls):
            if field.name not in values:
                continue
            raw_value = values[field.name]
            if field.name == "shelly_3em_base_url":
                current[field.name] = str(raw_value).strip()
            elif field.name in lowercase_string_fields:
                current[field.name] = str(raw_value).strip().lower()
            elif field.name in bool_fields:
                current[field.name] = parse_bool(raw_value)
            elif field.name in float_fields:
                current[field.name] = parse_float(raw_value, field.name)
            else:
                current[field.name] = parse_int(raw_value, field.name)
        settings = cls(**current)
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.ui_language not in {"de", "en"}:
            raise ValueError("ui_language must be 'de' or 'en'")
        if self.meter_provider not in {"mock", "shelly_3em"}:
            raise ValueError("meter_provider must be 'mock' or 'shelly_3em'")
        if self.meter_power_sign not in {"normal", "inverted"}:
            raise ValueError("meter_power_sign must be 'normal' or 'inverted'")
        if self.shelly_3em_generation not in {"auto", "gen1", "gen2"}:
            raise ValueError("shelly_3em_generation must be 'auto', 'gen1', or 'gen2'")
        if self.shelly_3em_timeout_seconds <= 0:
            raise ValueError("shelly_3em_timeout_seconds must be greater than 0")
        if self.meter_provider == "shelly_3em" and not self.shelly_3em_base_url:
            raise ValueError("shelly_3em_base_url is required when meter_provider=shelly_3em")
        if self.control_interval_seconds <= 0:
            raise ValueError("control_interval_seconds must be greater than 0")
        if self.stale_measurement_seconds <= 0:
            raise ValueError("stale_measurement_seconds must be greater than 0")
        if self.min_output_power_w < 0:
            raise ValueError("min_output_power_w must not be negative")
        if self.max_output_power_w < self.min_output_power_w:
            raise ValueError("max_output_power_w must be greater than or equal to min_output_power_w")
        if self.output_step_w <= 0:
            raise ValueError("output_step_w must be greater than 0")
        if self.min_output_change_w < 0:
            raise ValueError("min_output_change_w must not be negative")
        if self.grid_power_band_min_w > self.grid_power_band_max_w:
            raise ValueError("grid_power_band_min_w must be less than or equal to grid_power_band_max_w")
        if not 0 <= self.min_soc_percent <= 100:
            raise ValueError("min_soc_percent must be between 0 and 100")


@dataclass(slots=True)
class ControlDecision:
    timestamp: datetime
    current_output_power_w: int
    target_output_power_w: int
    grid_power_w: int | None
    battery_soc: int | None
    zero_export_enabled: bool
    control_mode: str
    reason: str
    error_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = datetime_to_iso(self.timestamp)
        return payload

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "ControlDecision":
        return cls(
            timestamp=datetime_from_iso(row["timestamp"]),
            current_output_power_w=int(row["current_output_power_w"]),
            target_output_power_w=int(row["target_output_power_w"]),
            grid_power_w=None if row["grid_power_w"] is None else int(row["grid_power_w"]),
            battery_soc=None if row["battery_soc"] is None else int(row["battery_soc"]),
            zero_export_enabled=parse_bool(row["zero_export_enabled"]),
            control_mode=str(row["control_mode"]),
            reason=str(row["reason"]),
            error_status=row["error_status"],
        )


def is_valid_number(value: Any) -> bool:
    return isinstance(value, int | float) and isfinite(value)
