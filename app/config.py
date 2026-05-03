from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from app.models import ControlSettings, parse_bool, parse_int


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
        self.control.validate()


def _empty_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None
