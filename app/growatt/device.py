from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import Measurement


class GrowattDevice(ABC):
    @abstractmethod
    async def get_latest_measurements(self) -> Measurement:
        """Return the most recent locally available measurements."""

    @abstractmethod
    async def set_output_power(self, target_power_w: int) -> None:
        """Set the target AC output power in watts."""

    @abstractmethod
    async def get_device_status(self) -> str:
        """Return a short device status such as online, offline, or error."""

