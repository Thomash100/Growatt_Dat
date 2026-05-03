from datetime import timedelta

from app.control import safety
from app.models import ControlSettings, Measurement, utc_now


def measurement(**overrides):
    defaults = {
        "timestamp": utc_now(),
        "pv_power_w": 700,
        "output_power_w": 400,
        "grid_power_w": 35,
        "battery_soc": 65,
        "charge_discharge_power_w": -120,
        "device_status": "online",
    }
    defaults.update(overrides)
    return Measurement(**defaults)


def test_safety_rejects_error_status_for_increase():
    result = safety.can_increase_output(measurement(device_status="error"), ControlSettings())

    assert result.ok is False
    assert result.reason == "device_error_status"


def test_safety_rejects_unknown_status_for_increase():
    result = safety.can_increase_output(measurement(device_status="unknown"), ControlSettings())

    assert result.ok is False
    assert result.reason == "unknown_device_status"


def test_safety_rejects_stale_measurement():
    result = safety.can_increase_output(
        measurement(timestamp=utc_now() - timedelta(seconds=20)),
        ControlSettings(stale_measurement_seconds=10),
        now=utc_now(),
    )

    assert result.ok is False
    assert result.reason == "stale_measurement"


def test_safety_clamps_target_output_to_limits():
    settings = ControlSettings(min_output_power_w=0, max_output_power_w=800)

    assert safety.clamp_output_power(-50, settings) == 0
    assert safety.clamp_output_power(850, settings) == 800

