from __future__ import annotations

import asyncio
import math
import random
from datetime import datetime

from app.growatt.device import GrowattDevice
from app.models import Measurement, utc_now


class MockGrowattDevice(GrowattDevice):
    def __init__(self, *, max_output_power_w: int = 800, seed: int | None = None) -> None:
        self._max_output_power_w = max_output_power_w
        self._random = random.Random(seed)
        self._target_output_power_w = 350
        self._actual_output_power_w = 330.0
        self._battery_soc = 64.0
        self._latest: Measurement | None = None
        self._status = "online"
        self._start_time = utc_now()
        self._lock = asyncio.Lock()

    async def poll(self) -> Measurement:
        async with self._lock:
            now = utc_now()
            elapsed = (now - self._start_time).total_seconds()
            phase = elapsed / 60.0

            pv_base = 520 + 220 * math.sin(phase / 2.2)
            pv_noise = self._random.uniform(-55, 75)
            pv_power_w = max(0, min(950, int(pv_base + pv_noise)))

            load_base = 380 + 120 * math.sin(phase * 1.7 + 1.3)
            load_spike = 180 if int(elapsed) % 47 in {0, 1, 2, 3} else 0
            house_load_w = max(120, int(load_base + load_spike + self._random.uniform(-70, 70)))

            self._actual_output_power_w += (self._target_output_power_w - self._actual_output_power_w) * 0.35
            self._actual_output_power_w += self._random.uniform(-8, 8)
            self._actual_output_power_w = max(0, min(self._max_output_power_w, self._actual_output_power_w))

            charge_discharge_power_w = int(pv_power_w - self._actual_output_power_w - 80)
            self._battery_soc += charge_discharge_power_w / 42000.0
            self._battery_soc += self._random.uniform(-0.02, 0.02)
            self._battery_soc = max(5, min(98, self._battery_soc))

            grid_power_w = int(house_load_w - self._actual_output_power_w + self._random.uniform(-18, 18))

            self._latest = Measurement(
                timestamp=now,
                pv_power_w=pv_power_w,
                output_power_w=int(self._actual_output_power_w),
                grid_power_w=grid_power_w,
                battery_soc=int(round(self._battery_soc)),
                charge_discharge_power_w=charge_discharge_power_w,
                device_status=self._status,
            )
            return self._latest

    async def get_latest_measurements(self) -> Measurement:
        if self._latest is None:
            return await self.poll()
        return self._latest

    async def set_output_power(self, target_power_w: int) -> None:
        async with self._lock:
            self._target_output_power_w = max(0, min(self._max_output_power_w, int(target_power_w)))

    async def get_device_status(self) -> str:
        return self._status

    @property
    def target_output_power_w(self) -> int:
        return self._target_output_power_w

