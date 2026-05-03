from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models import ControlSettings, Measurement, is_valid_number, utc_now


ERROR_STATUSES = {"error", "fault", "failed", "offline"}
UNKNOWN_STATUSES = {"unknown", "unavailable", ""}
SAFE_STATUSES = {"online", "ready", "running", "mock"}


@dataclass(frozen=True, slots=True)
class SafetyResult:
    ok: bool
    reason: str


def validate_measurement(measurement: Measurement | None) -> SafetyResult:
    if measurement is None:
        return SafetyResult(False, "missing_measurement")
    numeric_values = (
        measurement.pv_power_w,
        measurement.output_power_w,
        measurement.grid_power_w,
        measurement.battery_soc,
        measurement.charge_discharge_power_w,
    )
    if not all(is_valid_number(value) for value in numeric_values):
        return SafetyResult(False, "invalid_measurement")
    if not 0 <= measurement.battery_soc <= 100:
        return SafetyResult(False, "invalid_soc")
    return SafetyResult(True, "measurement_valid")


def measurement_is_fresh(
    measurement: Measurement,
    stale_after_seconds: int,
    *,
    now: datetime | None = None,
) -> SafetyResult:
    current_time = now or utc_now()
    age_seconds = (current_time - measurement.timestamp).total_seconds()
    if age_seconds < 0:
        return SafetyResult(False, "future_measurement")
    if age_seconds > stale_after_seconds:
        return SafetyResult(False, "stale_measurement")
    return SafetyResult(True, "measurement_fresh")


def soc_is_safe(measurement: Measurement, min_soc_percent: int) -> SafetyResult:
    if measurement.battery_soc < min_soc_percent:
        return SafetyResult(False, "soc_below_minimum")
    return SafetyResult(True, "soc_ok")


def target_within_limits(target_output_power_w: int, settings: ControlSettings) -> SafetyResult:
    if target_output_power_w < settings.min_output_power_w:
        return SafetyResult(False, "target_below_minimum")
    if target_output_power_w > settings.max_output_power_w:
        return SafetyResult(False, "target_above_maximum")
    return SafetyResult(True, "target_within_limits")


def clamp_output_power(target_output_power_w: int, settings: ControlSettings) -> int:
    return max(settings.min_output_power_w, min(settings.max_output_power_w, int(target_output_power_w)))


def device_allows_increase(measurement: Measurement) -> SafetyResult:
    status = measurement.device_status.strip().lower()
    if status in ERROR_STATUSES:
        return SafetyResult(False, "device_error_status")
    if status in UNKNOWN_STATUSES or status not in SAFE_STATUSES:
        return SafetyResult(False, "unknown_device_status")
    return SafetyResult(True, "device_allows_increase")


def can_increase_output(
    measurement: Measurement | None,
    settings: ControlSettings,
    *,
    now: datetime | None = None,
) -> SafetyResult:
    valid = validate_measurement(measurement)
    if not valid.ok:
        return valid
    assert measurement is not None
    fresh = measurement_is_fresh(measurement, settings.stale_measurement_seconds, now=now)
    if not fresh.ok:
        return fresh
    soc = soc_is_safe(measurement, settings.min_soc_percent)
    if not soc.ok:
        return soc
    status = device_allows_increase(measurement)
    if not status.ok:
        return status
    return SafetyResult(True, "increase_allowed")

