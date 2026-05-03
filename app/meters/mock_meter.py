from __future__ import annotations

import math
import random

from app.meters.device import EnergyMeter
from app.models import MeterReading, utc_now


class MockGridMeter(EnergyMeter):
    def __init__(self, *, seed: int | None = None, invert_sign: bool = False) -> None:
        self._random = random.Random(seed)
        self._start_time = utc_now()
        self._invert_sign = invert_sign

    async def get_latest_reading(self) -> MeterReading:
        now = utc_now()
        elapsed = (now - self._start_time).total_seconds()
        phase = elapsed / 45.0
        base = 40 + 130 * math.sin(phase)
        export_dip = -150 if int(elapsed) % 73 in range(0, 8) else 0
        grid_power_w = int(base + export_dip + self._random.uniform(-30, 30))
        if self._invert_sign:
            grid_power_w *= -1
        return MeterReading(
            timestamp=now,
            grid_power_w=grid_power_w,
            status="online",
            source="mock",
            phase_powers_w={
                "a": round(grid_power_w * 0.34, 1),
                "b": round(grid_power_w * 0.33, 1),
                "c": round(grid_power_w * 0.33, 1),
            },
        )

