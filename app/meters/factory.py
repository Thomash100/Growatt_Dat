from __future__ import annotations

from app.meters.device import EnergyMeter
from app.meters.mock_meter import MockGridMeter
from app.meters.shelly_3em import Shelly3EMMeter
from app.models import ControlSettings


def create_meter(settings: ControlSettings) -> EnergyMeter:
    invert_sign = settings.meter_power_sign == "inverted"
    if settings.meter_provider == "shelly_3em":
        return Shelly3EMMeter(
            base_url=settings.shelly_3em_base_url,
            generation=settings.shelly_3em_generation,
            timeout_seconds=settings.shelly_3em_timeout_seconds,
            invert_sign=invert_sign,
        )
    return MockGridMeter(invert_sign=invert_sign)
