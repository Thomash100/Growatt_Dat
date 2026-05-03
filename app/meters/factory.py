from __future__ import annotations

from app.config import AppConfig
from app.meters.device import EnergyMeter
from app.meters.mock_meter import MockGridMeter
from app.meters.shelly_3em import Shelly3EMMeter


def create_meter(config: AppConfig) -> EnergyMeter:
    invert_sign = config.meter_power_sign == "inverted"
    if config.meter_provider == "shelly_3em":
        assert config.shelly_3em_base_url is not None
        return Shelly3EMMeter(
            base_url=config.shelly_3em_base_url,
            generation=config.shelly_3em_generation,
            timeout_seconds=config.shelly_3em_timeout_seconds,
            invert_sign=invert_sign,
        )
    return MockGridMeter(invert_sign=invert_sign)
