from app.meters.shelly_3em import Shelly3EMMeter, ShellyMeterError


def test_shelly_gen1_status_parses_total_power_and_phases():
    reading = Shelly3EMMeter.parse_gen1_status(
        {
            "total_power": 123.4,
            "emeters": [
                {"power": 40.1, "is_valid": True},
                {"power": 41.2, "is_valid": True},
                {"power": 42.1, "is_valid": True},
            ],
        }
    )

    assert reading.grid_power_w == 123
    assert reading.source == "shelly_3em_gen1"
    assert reading.phase_powers_w["a"] == 40.1


def test_shelly_gen1_can_invert_power_sign():
    reading = Shelly3EMMeter.parse_gen1_status(
        {
            "total_power": 50,
            "emeters": [
                {"power": 10, "is_valid": True},
                {"power": 20, "is_valid": True},
                {"power": 20, "is_valid": True},
            ],
        },
        invert_sign=True,
    )

    assert reading.grid_power_w == -50


def test_shelly_gen1_rejects_invalid_phase():
    try:
        Shelly3EMMeter.parse_gen1_status(
            {
                "total_power": 50,
                "emeters": [
                    {"power": 10, "is_valid": True},
                    {"power": 20, "is_valid": False},
                    {"power": 20, "is_valid": True},
                ],
            }
        )
    except ShellyMeterError as exc:
        assert "invalid" in str(exc)
    else:
        raise AssertionError("Expected invalid Shelly phase to raise")


def test_shelly_gen2_status_parses_total_act_power():
    reading = Shelly3EMMeter.parse_gen2_status(
        {
            "total_act_power": -35.6,
            "a_act_power": -10.1,
            "b_act_power": -12.2,
            "c_act_power": -13.3,
        }
    )

    assert reading.grid_power_w == -36
    assert reading.source == "shelly_3em_gen2"
    assert reading.phase_powers_w["c"] == -13.3


def test_shelly_gen2_status_parses_rpc_result_wrapper():
    payload = {
        "result": {
            "total_act_power": 42,
            "a_act_power": 10,
            "b_act_power": 12,
            "c_act_power": 20,
        }
    }

    reading = Shelly3EMMeter.parse_gen2_status(payload["result"])

    assert reading.grid_power_w == 42
