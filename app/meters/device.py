from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import MeterReading


class EnergyMeter(ABC):
    @abstractmethod
    async def get_latest_reading(self) -> MeterReading:
        """Return the latest local grid-meter reading."""

