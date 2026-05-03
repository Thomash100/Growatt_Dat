from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
from math import isfinite
from typing import Any, Mapping


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


@dataclass(frozen=True, slots=True)
class ControlSettings:
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
        for field in fields(cls):
            if field.name not in values:
                continue
            raw_value = values[field.name]
            if field.name in bool_fields:
                current[field.name] = parse_bool(raw_value)
            else:
                current[field.name] = parse_int(raw_value, field.name)
        settings = cls(**current)
        settings.validate()
        return settings

    def validate(self) -> None:
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
