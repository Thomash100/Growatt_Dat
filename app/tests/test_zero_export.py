from datetime import timedelta

from app.control.zero_export import ZeroExportController
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


def decide(item, settings=ControlSettings()):
    return ZeroExportController().decide(item, settings, now=utc_now())


def test_zero_export_within_deadband_keeps_output():
    decision = decide(measurement(grid_power_w=35, output_power_w=420))

    assert decision.reason == "within_deadband"
    assert decision.target_output_power_w == 420


def test_zero_export_reduces_when_exporting():
    decision = decide(measurement(grid_power_w=-50, output_power_w=420))

    assert decision.reason == "reduce_export"
    assert decision.target_output_power_w == 370


def test_zero_export_increases_when_import_is_high():
    decision = decide(measurement(grid_power_w=150, output_power_w=420))

    assert decision.reason == "increase_due_to_import"
    assert decision.target_output_power_w == 470


def test_zero_export_reduces_when_soc_is_below_minimum():
    decision = decide(measurement(battery_soc=10, output_power_w=420, grid_power_w=150))

    assert decision.reason == "soc_below_minimum"
    assert decision.target_output_power_w == 370
    assert decision.error_status == "soc_below_minimum"


def test_zero_export_reduces_when_measurement_is_stale():
    settings = ControlSettings(stale_measurement_seconds=10)
    stale = measurement(timestamp=utc_now() - timedelta(seconds=30), grid_power_w=150, output_power_w=420)

    decision = ZeroExportController().decide(stale, settings, now=utc_now())

    assert decision.reason == "stale_measurement"
    assert decision.target_output_power_w == 370
    assert decision.error_status == "stale_measurement"


def test_zero_export_clamps_to_maximum_output_power():
    decision = decide(measurement(grid_power_w=150, output_power_w=790))

    assert decision.reason == "increase_due_to_import"
    assert decision.target_output_power_w == 800


def test_zero_export_clamps_to_minimum_output_power():
    decision = decide(measurement(grid_power_w=-80, output_power_w=20))

    assert decision.reason == "reduce_export"
    assert decision.target_output_power_w == 0


def test_zero_export_disabled_keeps_current_output():
    settings = ControlSettings(zero_export_enabled=False)

    decision = decide(measurement(grid_power_w=180, output_power_w=420), settings)

    assert decision.reason == "zero_export_disabled"
    assert decision.control_mode == "manual"
    assert decision.target_output_power_w == 420

