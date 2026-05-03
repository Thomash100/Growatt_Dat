from __future__ import annotations

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import AppConfig
from app.control.zero_export import ZeroExportController
from app.growatt.mock_device import MockGrowattDevice
from app.logging_config import configure_logging
from app.models import ControlDecision, ControlSettings, Measurement, datetime_to_iso, utc_now
from app.mqtt.publisher import MqttPublisher
from app.storage.sqlite_store import SQLiteStore
from app.web.routes import router
from app.web.websocket import register_websocket_routes


configure_logging()
LOGGER = logging.getLogger("growatt_gateway")


class GatewayService:
    def __init__(self, config: AppConfig, store: SQLiteStore, settings: ControlSettings) -> None:
        self.config = config
        self.store = store
        self.settings = settings
        self.device = MockGrowattDevice(max_output_power_w=settings.max_output_power_w)
        self.controller = ZeroExportController()
        self.mqtt = MqttPublisher(config)
        self.latest_measurement: Measurement | None = None
        self.latest_decision: ControlDecision | None = None
        self.error_status: str | None = None
        self.started_at = utc_now()
        self._task: asyncio.Task[None] | None = None
        self._settings_lock = asyncio.Lock()

    async def start(self) -> None:
        self.mqtt.start()
        self.mqtt.publish_settings(self.settings)
        self.store.add_log("INFO", "system", "Gateway service started with mock Growatt device")
        self._task = asyncio.create_task(self._run_forever(), name="gateway-control-loop")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.mqtt.stop()
        self.store.add_log("INFO", "system", "Gateway service stopped")

    async def update_settings(self, settings: ControlSettings) -> None:
        async with self._settings_lock:
            self.settings = settings
            self.store.save_settings(settings)
            self.mqtt.publish_settings(settings)
            self.store.add_log("INFO", "system", "Settings updated")

    def snapshot(self) -> dict[str, Any]:
        status_payload = self._status_payload()
        return {
            "timestamp": datetime_to_iso(utc_now()),
            "measurements": None if self.latest_measurement is None else self.latest_measurement.to_dict(),
            "control": None if self.latest_decision is None else self.latest_decision.to_dict(),
            "settings": self.settings.to_dict(),
            "device_status": status_payload["device_status"],
            "error_status": self.error_status,
            "status": status_payload,
        }

    async def _run_forever(self) -> None:
        while True:
            started = time.monotonic()
            try:
                async with self._settings_lock:
                    self.settings = self.store.load_settings(self.settings)
                await self._run_cycle()
                self.error_status = None
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.error_status = str(exc)
                LOGGER.exception("Gateway cycle failed")
                self.store.add_log("ERROR", "error", f"Gateway cycle failed: {exc}")

            elapsed = time.monotonic() - started
            sleep_seconds = max(0.5, self.settings.control_interval_seconds - elapsed)
            await asyncio.sleep(sleep_seconds)

    async def _run_cycle(self) -> None:
        measurement = await self.device.poll()
        self.latest_measurement = measurement
        self.store.save_measurement(measurement)

        decision = self.controller.decide(measurement, self.settings)
        await self.device.set_output_power(decision.target_output_power_w)
        self.latest_decision = decision
        self.store.save_control_decision(decision)
        self.store.add_log(
            "INFO",
            "control",
            f"{decision.reason}: {decision.current_output_power_w} W -> {decision.target_output_power_w} W",
        )

        self.mqtt.publish_measurement(measurement)
        self.mqtt.publish_control(decision)
        self.mqtt.publish_settings(self.settings)
        self.mqtt.publish_status(self._status_payload())
        self.mqtt.publish_state(self.snapshot())

    def _status_payload(self) -> dict[str, Any]:
        uptime_seconds = int((utc_now() - self.started_at).total_seconds())
        return {
            "timestamp": datetime_to_iso(utc_now()),
            "device_status": "unknown" if self.latest_measurement is None else self.latest_measurement.device_status,
            "mqtt_connected": self.mqtt.connected,
            "error_status": self.error_status,
            "uptime_seconds": uptime_seconds,
        }


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = AppConfig.from_env()
    store = SQLiteStore(config.database_path)
    store.init_db()
    if not store.get_logs(limit=1):
        store.add_log("INFO", "system", "Database initialized")
    settings = store.load_settings(config.control)
    store.save_settings(settings)
    service = GatewayService(config, store, settings)
    app.state.service = service
    await service.start()
    try:
        yield
    finally:
        await service.stop()
        store.close()


app = FastAPI(
    title="Growatt Local Gateway",
    description="Local mock gateway for future Growatt NEO/NOAH integration",
    version="0.1.0",
    lifespan=lifespan,
)

static_dir = Path(__file__).parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.include_router(router)
register_websocket_routes(app)

