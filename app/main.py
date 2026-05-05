from __future__ import annotations

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import AppConfig
from app.control.zero_export import ZeroExportController
from app.growatt.mock_device import MockGrowattDevice
from app.integrations.scanner import IntegrationScanner
from app.logging_config import configure_logging
from app.meters.factory import create_meter
from app.meters.shelly_generic import ShellyGenericReader
from app.models import (
    ControlDecision,
    ControlSettings,
    DailyEnergySummary,
    Measurement,
    MeterReading,
    ShellyDeviceConfig,
    ShellyDeviceReading,
    datetime_to_iso,
    utc_now,
)
from app.mqtt.publisher import MqttPublisher
from app.storage.sqlite_store import SQLiteStore
from app.update_checker import UpdateChecker
from app.version import VERSION, VERSION_LABEL
from app.web_update import WebUpdater, new_update_job
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
        self.meter = create_meter(settings)
        self.controller = ZeroExportController()
        self.mqtt = MqttPublisher(config)
        self.update_checker = UpdateChecker(
            config.update_repository,
            timeout_seconds=config.update_check_timeout_seconds,
            enabled=config.update_check_enabled,
        )
        self.integration_scanner = IntegrationScanner(
            timeout_seconds=config.integration_scan_timeout_seconds,
            concurrency=config.integration_scan_concurrency,
            max_hosts=config.integration_scan_max_hosts,
        )
        self.web_updater = WebUpdater(config.web_update)
        self.shelly_reader = ShellyGenericReader()
        self.latest_measurement: Measurement | None = None
        self.latest_meter_reading: MeterReading | None = None
        self.latest_shelly_readings: dict[str, ShellyDeviceReading] = store.get_latest_shelly_readings()
        self.latest_daily_energy: DailyEnergySummary | None = store.get_daily_energy(utc_now().astimezone().date().isoformat())
        self.latest_decision: ControlDecision | None = None
        self.error_status: str | None = None
        self.started_at = utc_now()
        self._task: asyncio.Task[None] | None = None
        self._settings_lock = asyncio.Lock()
        self._update_cache: tuple[float, dict[str, Any]] | None = None
        self._web_update_task: asyncio.Task[None] | None = None
        self._web_update_job = None
        self._previous_energy_measurement: Measurement | None = None
        self._previous_shelly_summary: dict[str, Any] | None = None

    async def start(self) -> None:
        self.mqtt.start()
        self.mqtt.publish_settings(self.settings)
        self.store.add_log(
            "INFO",
            "system",
            f"Gateway service started with {self.settings.meter_provider} grid meter",
        )
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
            meter_changed = self._meter_settings_changed(self.settings, settings)
            self.settings = settings
            if meter_changed:
                self.meter = create_meter(settings)
                self.latest_meter_reading = None
                self.store.add_log("INFO", "meter", f"Grid meter reconfigured to {settings.meter_provider}")
            self.store.save_settings(settings)
            self.mqtt.publish_settings(settings)
            self.store.add_log("INFO", "system", "Settings updated")

    async def check_updates(self, *, force: bool = False) -> dict[str, Any]:
        if not force and self._update_cache is not None:
            checked_at, cached = self._update_cache
            if time.monotonic() - checked_at < 900:
                return cached
        result = await asyncio.to_thread(self.update_checker.check)
        payload = result.to_dict()
        self._update_cache = (time.monotonic(), payload)
        if payload.get("update_available"):
            self.store.add_log("INFO", "system", f"Update available: {payload.get('latest_version_label')}")
        return payload

    def web_update_status(self) -> dict[str, Any]:
        return {
            "availability": self.web_updater.availability(),
            "running": self._web_update_task is not None and not self._web_update_task.done(),
            "job": None if self._web_update_job is None else self._web_update_job.to_dict(),
        }

    async def start_web_update(self, token: str | None) -> dict[str, Any]:
        if not self.web_updater.verify_token(token):
            raise ValueError("invalid_update_token")
        if self._web_update_task is not None and not self._web_update_task.done():
            raise ValueError("web_update_already_running")

        job = new_update_job()
        self._web_update_job = job
        self._web_update_task = asyncio.create_task(self._run_web_update_job(job), name="web-update")
        self.store.add_log("INFO", "system", f"Web update started: {job.id}")
        return self.web_update_status()

    async def _run_web_update_job(self, job) -> None:
        await self.web_updater.run(job)
        self.store.add_log("INFO" if job.status == "succeeded" else "ERROR", "system", f"Web update {job.status}")

    async def scan_integrations(self, cidr: str | None = None) -> dict[str, Any]:
        scan_range = cidr or self.config.integration_scan_default_cidr
        result = await self.integration_scanner.scan(scan_range)
        payload = result.to_dict()
        self.store.add_log(
            "INFO",
            "system",
            f"Integration scan {payload['cidr']}: {len(payload['candidates'])} candidate(s)",
        )
        return payload

    async def apply_integration(self, payload: dict[str, Any]) -> dict[str, Any]:
        integration_type = str(payload.get("integration_type", "")).strip().lower()
        if integration_type != "shelly_3em":
            raise ValueError("Only shelly_3em integration apply is supported")
        base_url = str(payload.get("base_url", "")).strip().rstrip("/")
        generation = str(payload.get("generation", "auto")).strip().lower()
        if not base_url.startswith("http://"):
            raise ValueError("base_url must start with http://")
        if generation not in {"auto", "gen1", "gen2"}:
            raise ValueError("generation must be auto, gen1, or gen2")

        updated = ControlSettings.from_mapping(
            {
                "meter_provider": "shelly_3em",
                "shelly_3em_base_url": base_url,
                "shelly_3em_generation": generation,
                "meter_power_sign": payload.get("meter_power_sign", self.settings.meter_power_sign),
            },
            base=self.settings,
        )
        await self.update_settings(updated)
        self.store.add_log("INFO", "system", f"Integration applied: shelly_3em at {base_url}")
        return updated.to_dict()

    async def add_shelly_device(self, payload: dict[str, Any]) -> dict[str, Any]:
        prepared = self._prepare_shelly_device_payload(payload)
        device = ShellyDeviceConfig.from_mapping(prepared)
        saved = self.store.save_shelly_device(device)
        self.store.add_log("INFO", "shelly", f"Shelly device added: {saved.name} at {saved.base_url}")
        await self._read_shelly_device(saved)
        return self.shelly_devices_payload()

    async def update_shelly_device(self, device_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.store.get_shelly_device(device_id)
        if current is None:
            raise ValueError("shelly_device_not_found")
        prepared = self._prepare_shelly_device_payload(payload, base=current)
        updated = ShellyDeviceConfig.from_mapping(prepared, base=current)
        saved = self.store.save_shelly_device(updated)
        self.store.add_log("INFO", "shelly", f"Shelly device updated: {saved.name}")
        if saved.enabled:
            await self._read_shelly_device(saved)
        return self.shelly_devices_payload()

    async def delete_shelly_device(self, device_id: str) -> dict[str, Any]:
        if not self.store.delete_shelly_device(device_id):
            raise ValueError("shelly_device_not_found")
        self.latest_shelly_readings.pop(device_id, None)
        self.store.add_log("INFO", "shelly", f"Shelly device removed: {device_id}")
        return self.shelly_devices_payload()

    def shelly_devices_payload(self) -> dict[str, Any]:
        devices = self.store.list_shelly_devices()
        return {
            "devices": [self._shelly_device_payload(device) for device in devices],
            "summary": self._shelly_summary(devices),
        }

    def snapshot(self) -> dict[str, Any]:
        status_payload = self._status_payload()
        return {
            "timestamp": datetime_to_iso(utc_now()),
            "version": VERSION_LABEL,
            "measurements": None if self.latest_measurement is None else self.latest_measurement.to_dict(),
            "meter": None if self.latest_meter_reading is None else self.latest_meter_reading.to_dict(),
            "shelly_devices": self.shelly_devices_payload()["devices"],
            "shelly_summary": self.shelly_devices_payload()["summary"],
            "daily_energy_today": None if self.latest_daily_energy is None else self.latest_daily_energy.to_dict(),
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
        device_measurement = await self.device.poll()
        meter_reading = await self._read_meter()
        await self._read_shelly_devices()
        measurement = replace(device_measurement, grid_power_w=meter_reading.grid_power_w)
        self.latest_measurement = measurement
        self.latest_meter_reading = meter_reading
        self.store.save_measurement(measurement)
        self._update_daily_energy(measurement)

        if meter_reading.error_status:
            decision = ControlDecision(
                timestamp=utc_now(),
                current_output_power_w=measurement.output_power_w,
                target_output_power_w=measurement.output_power_w,
                grid_power_w=measurement.grid_power_w,
                battery_soc=measurement.battery_soc,
                zero_export_enabled=self.settings.zero_export_enabled,
                control_mode="zero_export",
                reason="meter_unavailable",
                error_status=meter_reading.error_status,
            )
        else:
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
        self.mqtt.publish_shelly_devices(self.shelly_devices_payload())
        if self.latest_daily_energy is not None:
            self.mqtt.publish_statistics({"daily_energy_today": self.latest_daily_energy.to_dict()})
        self.mqtt.publish_state(self.snapshot())

    def _status_payload(self) -> dict[str, Any]:
        uptime_seconds = int((utc_now() - self.started_at).total_seconds())
        return {
            "timestamp": datetime_to_iso(utc_now()),
            "version": VERSION_LABEL,
            "device_status": "unknown" if self.latest_measurement is None else self.latest_measurement.device_status,
            "meter_provider": self.settings.meter_provider,
            "meter_source": None if self.latest_meter_reading is None else self.latest_meter_reading.source,
            "meter_status": "unknown" if self.latest_meter_reading is None else self.latest_meter_reading.status,
            "shelly_devices": self.shelly_devices_payload()["summary"],
            "daily_energy_today": None if self.latest_daily_energy is None else self.latest_daily_energy.to_dict(),
            "mqtt_connected": self.mqtt.connected,
            "error_status": self.error_status,
            "uptime_seconds": uptime_seconds,
        }

    async def _read_meter(self) -> MeterReading:
        try:
            return await self.meter.get_latest_reading()
        except Exception as exc:
            LOGGER.exception("Grid meter read failed")
            self.store.add_log("ERROR", "meter", f"Grid meter read failed: {exc}")
            fallback_power = 0 if self.latest_measurement is None else self.latest_measurement.grid_power_w
            return MeterReading(
                timestamp=utc_now(),
                grid_power_w=fallback_power,
                status="error",
                source=self.settings.meter_provider,
                phase_powers_w={},
                error_status=str(exc),
            )

    @staticmethod
    def _meter_settings_changed(previous: ControlSettings, updated: ControlSettings) -> bool:
        return any(
            getattr(previous, field) != getattr(updated, field)
            for field in (
                "meter_provider",
                "meter_power_sign",
                "shelly_3em_base_url",
                "shelly_3em_generation",
                "shelly_3em_timeout_seconds",
            )
        )

    async def _read_shelly_devices(self) -> None:
        devices = self.store.list_shelly_devices(enabled_only=True)
        if not devices:
            return
        await asyncio.gather(*(self._read_shelly_device(device) for device in devices))

    async def _read_shelly_device(self, device: ShellyDeviceConfig) -> None:
        try:
            reading = await self.shelly_reader.read(device)
        except Exception as exc:
            reading = ShellyDeviceReading(
                timestamp=utc_now(),
                device_id=device.id,
                name=device.name,
                role=device.role,
                base_url=device.base_url,
                generation=device.generation,
                model=device.model,
                status="error",
                raw_values={},
                error_status=str(exc),
            )
            self.store.add_log("ERROR", "shelly", f"Shelly read failed for {device.name}: {exc}")
        self.latest_shelly_readings[device.id] = reading
        self.store.save_shelly_reading(reading)

    def _shelly_device_payload(self, device: ShellyDeviceConfig) -> dict[str, Any]:
        payload = device.to_dict()
        reading = self.latest_shelly_readings.get(device.id)
        payload["reading"] = None if reading is None else reading.to_dict()
        return payload

    def _shelly_summary(self, devices: list[ShellyDeviceConfig]) -> dict[str, Any]:
        role_powers = {role: 0.0 for role in ("pv", "load", "battery", "other")}
        online_count = 0
        error_count = 0
        enabled_count = 0
        for device in devices:
            if device.enabled:
                enabled_count += 1
            reading = self.latest_shelly_readings.get(device.id)
            if reading is None:
                continue
            if reading.status == "online":
                online_count += 1
            if reading.error_status:
                error_count += 1
            if reading.power_w is not None and device.role in role_powers:
                role_powers[device.role] += reading.power_w
        return {
            "configured_count": len(devices),
            "enabled_count": enabled_count,
            "online_count": online_count,
            "error_count": error_count,
            "pv_power_w": round(role_powers["pv"], 1),
            "load_power_w": round(role_powers["load"], 1),
            "battery_power_w": round(role_powers["battery"], 1),
            "other_power_w": round(role_powers["other"], 1),
            "total_power_w": round(sum(role_powers.values()), 1),
        }

    def _update_daily_energy(self, measurement: Measurement) -> None:
        current_summary = self.shelly_devices_payload()["summary"]
        if self._previous_energy_measurement is None:
            self._previous_energy_measurement = measurement
            self._previous_shelly_summary = current_summary
            self.latest_daily_energy = self.store.get_daily_energy(measurement.timestamp.astimezone().date().isoformat())
            return

        previous = self._previous_energy_measurement
        elapsed_seconds = (measurement.timestamp - previous.timestamp).total_seconds()
        max_gap_seconds = max(60.0, float(self.settings.control_interval_seconds) * 3.0)
        if elapsed_seconds <= 0 or elapsed_seconds > max_gap_seconds:
            self._previous_energy_measurement = measurement
            self._previous_shelly_summary = current_summary
            self.latest_daily_energy = self.store.get_daily_energy(measurement.timestamp.astimezone().date().isoformat())
            return

        hours = elapsed_seconds / 3600.0
        previous_summary = self._previous_shelly_summary or {}
        self.latest_daily_energy = self.store.add_daily_energy(
            measurement.timestamp.astimezone().date().isoformat(),
            pv_energy_wh=average_positive(previous.pv_power_w, measurement.pv_power_w) * hours,
            output_energy_wh=average_positive(previous.output_power_w, measurement.output_power_w) * hours,
            grid_import_wh=average_positive(previous.grid_power_w, measurement.grid_power_w) * hours,
            grid_export_wh=average_positive(-previous.grid_power_w, -measurement.grid_power_w) * hours,
            battery_charge_wh=average_positive(
                previous.charge_discharge_power_w,
                measurement.charge_discharge_power_w,
            )
            * hours,
            battery_discharge_wh=average_positive(
                -previous.charge_discharge_power_w,
                -measurement.charge_discharge_power_w,
            )
            * hours,
            shelly_pv_energy_wh=average_positive(
                float(previous_summary.get("pv_power_w", 0.0)),
                float(current_summary.get("pv_power_w", 0.0)),
            )
            * hours,
            shelly_load_energy_wh=average_positive(
                float(previous_summary.get("load_power_w", 0.0)),
                float(current_summary.get("load_power_w", 0.0)),
            )
            * hours,
            shelly_battery_charge_wh=average_positive(
                float(previous_summary.get("battery_power_w", 0.0)),
                float(current_summary.get("battery_power_w", 0.0)),
            )
            * hours,
            shelly_battery_discharge_wh=average_positive(
                -float(previous_summary.get("battery_power_w", 0.0)),
                -float(current_summary.get("battery_power_w", 0.0)),
            )
            * hours,
            shelly_other_energy_wh=average_positive(
                float(previous_summary.get("other_power_w", 0.0)),
                float(current_summary.get("other_power_w", 0.0)),
            )
            * hours,
        )
        self._previous_energy_measurement = measurement
        self._previous_shelly_summary = current_summary

    @staticmethod
    def _prepare_shelly_device_payload(
        payload: dict[str, Any],
        *,
        base: ShellyDeviceConfig | None = None,
    ) -> dict[str, Any]:
        base_url = str(payload.get("base_url", "" if base is None else base.base_url)).strip().rstrip("/")
        name = str(payload.get("name", "" if base is None else base.name)).strip()
        if not name and base_url:
            name = base_url.removeprefix("http://")
        return {
            "id": payload.get("id") or (base.id if base else str(uuid.uuid4())),
            "name": name,
            "base_url": base_url,
            "generation": payload.get("generation", base.generation if base else "auto"),
            "model": payload.get("model", base.model if base else None),
            "role": payload.get("role", base.role if base else "pv"),
            "power_sign": payload.get("power_sign", base.power_sign if base else "normal"),
            "enabled": payload.get("enabled", base.enabled if base else True),
            "timeout_seconds": payload.get("timeout_seconds", base.timeout_seconds if base else 3.0),
            "unique_id": payload.get("unique_id", base.unique_id if base else None),
            "created_at": None if base is None else base.created_at,
        }


def average_positive(previous_power_w: float, current_power_w: float) -> float:
    return max(0.0, (float(previous_power_w) + float(current_power_w)) / 2.0)


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
    version=VERSION,
    lifespan=lifespan,
)

static_dir = Path(__file__).parent / "web" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
app.include_router(router)
register_websocket_routes(app)
