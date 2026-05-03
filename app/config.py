from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from app.models import ControlSettings, parse_bool, parse_float, parse_int
from app.web_update import WebUpdateSettings
from app.version import PROJECT_REPOSITORY


def load_dotenv_file(path: str | Path = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True, slots=True)
class AppConfig:
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic_prefix: str = "growatt_local_gateway"
    mqtt_discovery_prefix: str = "homeassistant"
    database_path: str = "/data/growatt_gateway.sqlite"
    web_port: int = 8080
    meter_provider: str = "mock"
    meter_power_sign: str = "normal"
    shelly_3em_base_url: str | None = None
    shelly_3em_generation: str = "auto"
    shelly_3em_timeout_seconds: float = 3.0
    update_check_enabled: bool = True
    update_repository: str = PROJECT_REPOSITORY
    update_check_timeout_seconds: float = 4.0
    integration_scan_default_cidr: str = "192.168.178.0/24"
    integration_scan_timeout_seconds: float = 0.6
    integration_scan_concurrency: int = 32
    integration_scan_max_hosts: int = 254
    web_update: WebUpdateSettings = WebUpdateSettings()
    control: ControlSettings = ControlSettings()

    @classmethod
    def from_env(
        cls,
        env: Mapping[str, str] | None = None,
        *,
        load_dotenv: bool = True,
        dotenv_path: str | Path = ".env",
    ) -> "AppConfig":
        if load_dotenv and env is None:
            load_dotenv_file(dotenv_path)
        source = env or os.environ
        defaults = ControlSettings()

        control = ControlSettings.from_mapping(
            {
                "ui_language": source.get("UI_LANGUAGE", defaults.ui_language),
                "meter_provider": source.get("METER_PROVIDER", defaults.meter_provider),
                "meter_power_sign": source.get("METER_POWER_SIGN", defaults.meter_power_sign),
                "shelly_3em_base_url": source.get("SHELLY_3EM_BASE_URL", defaults.shelly_3em_base_url),
                "shelly_3em_generation": source.get("SHELLY_3EM_GENERATION", defaults.shelly_3em_generation),
                "shelly_3em_timeout_seconds": source.get(
                    "SHELLY_3EM_TIMEOUT_SECONDS",
                    defaults.shelly_3em_timeout_seconds,
                ),
                "zero_export_enabled": source.get("ZERO_EXPORT_ENABLED", defaults.zero_export_enabled),
                "target_grid_power_w": source.get("TARGET_GRID_POWER_W", defaults.target_grid_power_w),
                "grid_power_band_min_w": source.get("GRID_POWER_BAND_MIN_W", defaults.grid_power_band_min_w),
                "grid_power_band_max_w": source.get("GRID_POWER_BAND_MAX_W", defaults.grid_power_band_max_w),
                "control_interval_seconds": source.get(
                    "CONTROL_INTERVAL_SECONDS",
                    defaults.control_interval_seconds,
                ),
                "min_output_change_w": source.get("MIN_OUTPUT_CHANGE_W", defaults.min_output_change_w),
                "output_step_w": source.get("OUTPUT_STEP_W", defaults.output_step_w),
                "max_output_power_w": source.get("MAX_OUTPUT_POWER_W", defaults.max_output_power_w),
                "min_output_power_w": source.get("MIN_OUTPUT_POWER_W", defaults.min_output_power_w),
                "min_soc_percent": source.get("MIN_SOC_PERCENT", defaults.min_soc_percent),
                "stale_measurement_seconds": source.get(
                    "STALE_MEASUREMENT_SECONDS",
                    defaults.stale_measurement_seconds,
                ),
            }
        )

        config = cls(
            mqtt_host=str(source.get("MQTT_HOST", "localhost")),
            mqtt_port=parse_int(source.get("MQTT_PORT", 1883), "MQTT_PORT"),
            mqtt_username=_empty_to_none(source.get("MQTT_USERNAME")),
            mqtt_password=_empty_to_none(source.get("MQTT_PASSWORD")),
            mqtt_topic_prefix=str(source.get("MQTT_TOPIC_PREFIX", "growatt_local_gateway")).strip("/"),
            mqtt_discovery_prefix=str(source.get("MQTT_DISCOVERY_PREFIX", "homeassistant")).strip("/"),
            database_path=str(source.get("DATABASE_PATH", "/data/growatt_gateway.sqlite")),
            web_port=parse_int(source.get("WEB_PORT", 8080), "WEB_PORT"),
            meter_provider=control.meter_provider,
            meter_power_sign=control.meter_power_sign,
            shelly_3em_base_url=control.shelly_3em_base_url,
            shelly_3em_generation=control.shelly_3em_generation,
            shelly_3em_timeout_seconds=control.shelly_3em_timeout_seconds,
            update_check_enabled=parse_bool(source.get("UPDATE_CHECK_ENABLED", "true")),
            update_repository=str(source.get("UPDATE_REPOSITORY", PROJECT_REPOSITORY)).strip(),
            update_check_timeout_seconds=parse_float(
                source.get("UPDATE_CHECK_TIMEOUT_SECONDS", 4.0),
                "UPDATE_CHECK_TIMEOUT_SECONDS",
            ),
            integration_scan_default_cidr=str(
                source.get("INTEGRATION_SCAN_DEFAULT_CIDR", "192.168.178.0/24")
            ).strip(),
            integration_scan_timeout_seconds=parse_float(
                source.get("INTEGRATION_SCAN_TIMEOUT_SECONDS", 0.6),
                "INTEGRATION_SCAN_TIMEOUT_SECONDS",
            ),
            integration_scan_concurrency=parse_int(
                source.get("INTEGRATION_SCAN_CONCURRENCY", 32),
                "INTEGRATION_SCAN_CONCURRENCY",
            ),
            integration_scan_max_hosts=parse_int(
                source.get("INTEGRATION_SCAN_MAX_HOSTS", 254),
                "INTEGRATION_SCAN_MAX_HOSTS",
            ),
            web_update=WebUpdateSettings.from_mapping(
                {
                    "WEB_UPDATE_ENABLED": source.get("WEB_UPDATE_ENABLED", "false"),
                    "WEB_UPDATE_TOKEN": source.get("WEB_UPDATE_TOKEN", ""),
                    "WEB_UPDATE_WORKDIR": source.get("WEB_UPDATE_WORKDIR", "/app"),
                    "WEB_UPDATE_COMMAND_TIMEOUT_SECONDS": source.get(
                        "WEB_UPDATE_COMMAND_TIMEOUT_SECONDS",
                        "600",
                    ),
                    "WEB_UPDATE_REQUIRE_CLEAN_TREE": source.get("WEB_UPDATE_REQUIRE_CLEAN_TREE", "true"),
                    "WEB_UPDATE_RUN_DOCKER_COMPOSE": source.get("WEB_UPDATE_RUN_DOCKER_COMPOSE", "true"),
                    "WEB_UPDATE_RESTART_AFTER_SUCCESS": source.get("WEB_UPDATE_RESTART_AFTER_SUCCESS", "false"),
                }
            ),
            control=control,
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not 0 < self.mqtt_port < 65536:
            raise ValueError("MQTT_PORT must be between 1 and 65535")
        if not 0 < self.web_port < 65536:
            raise ValueError("WEB_PORT must be between 1 and 65535")
        if not self.mqtt_topic_prefix:
            raise ValueError("MQTT_TOPIC_PREFIX must not be empty")
        if not self.mqtt_discovery_prefix:
            raise ValueError("MQTT_DISCOVERY_PREFIX must not be empty")
        if self.meter_provider not in {"mock", "shelly_3em"}:
            raise ValueError("METER_PROVIDER must be 'mock' or 'shelly_3em'")
        if self.meter_power_sign not in {"normal", "inverted"}:
            raise ValueError("METER_POWER_SIGN must be 'normal' or 'inverted'")
        if self.shelly_3em_generation not in {"auto", "gen1", "gen2"}:
            raise ValueError("SHELLY_3EM_GENERATION must be 'auto', 'gen1', or 'gen2'")
        if self.shelly_3em_timeout_seconds <= 0:
            raise ValueError("SHELLY_3EM_TIMEOUT_SECONDS must be greater than 0")
        if not self.update_repository or "/" not in self.update_repository:
            raise ValueError("UPDATE_REPOSITORY must use the 'owner/repository' format")
        if self.update_check_timeout_seconds <= 0:
            raise ValueError("UPDATE_CHECK_TIMEOUT_SECONDS must be greater than 0")
        if not self.integration_scan_default_cidr:
            raise ValueError("INTEGRATION_SCAN_DEFAULT_CIDR must not be empty")
        if self.integration_scan_timeout_seconds <= 0:
            raise ValueError("INTEGRATION_SCAN_TIMEOUT_SECONDS must be greater than 0")
        if self.integration_scan_concurrency <= 0:
            raise ValueError("INTEGRATION_SCAN_CONCURRENCY must be greater than 0")
        if not 1 <= self.integration_scan_max_hosts <= 512:
            raise ValueError("INTEGRATION_SCAN_MAX_HOSTS must be between 1 and 512")
        if self.meter_provider == "shelly_3em" and not self.shelly_3em_base_url:
            raise ValueError("SHELLY_3EM_BASE_URL is required when METER_PROVIDER=shelly_3em")
        self.web_update.validate()
        self.control.validate()


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
