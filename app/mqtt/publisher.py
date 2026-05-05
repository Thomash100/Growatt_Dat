from __future__ import annotations

import json
import logging
from typing import Any

from app.config import AppConfig
from app.models import ControlDecision, ControlSettings, Measurement
from app.mqtt.discovery import build_discovery_payloads

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - exercised only without dependencies installed
    mqtt = None


LOGGER = logging.getLogger("growatt_gateway.mqtt")


class MqttPublisher:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.connected = False
        self._client: Any | None = None

    def start(self) -> None:
        if mqtt is None:
            LOGGER.warning("paho-mqtt is not installed; MQTT publishing disabled")
            return
        try:
            self._client = self._create_client()
            if self.config.mqtt_username:
                self._client.username_pw_set(self.config.mqtt_username, self.config.mqtt_password)
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.connect_async(self.config.mqtt_host, self.config.mqtt_port, keepalive=30)
            self._client.loop_start()
            LOGGER.info("MQTT publisher started for %s:%s", self.config.mqtt_host, self.config.mqtt_port)
        except Exception:
            LOGGER.exception("Failed to start MQTT publisher")

    def stop(self) -> None:
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception:
            LOGGER.exception("Failed to stop MQTT publisher")

    def publish_discovery(self) -> None:
        for topic, payload in build_discovery_payloads(
            topic_prefix=self.config.mqtt_topic_prefix,
            discovery_prefix=self.config.mqtt_discovery_prefix,
        ):
            self.publish_json(topic, payload, retain=True, absolute_topic=True)

    def publish_measurement(self, measurement: Measurement) -> None:
        self.publish_json("measurements", measurement.to_dict())

    def publish_control(self, decision: ControlDecision) -> None:
        self.publish_json("control", decision.to_dict())

    def publish_settings(self, settings: ControlSettings) -> None:
        self.publish_json("settings", settings.to_dict(), retain=True)

    def publish_status(self, payload: dict[str, Any]) -> None:
        self.publish_json("status", payload)

    def publish_state(self, payload: dict[str, Any]) -> None:
        self.publish_json("state", payload)

    def publish_shelly_devices(self, payload: dict[str, Any]) -> None:
        self.publish_json("shelly", payload)

    def publish_statistics(self, payload: dict[str, Any]) -> None:
        self.publish_json("statistics", payload, retain=True)

    def publish_json(self, topic: str, payload: dict[str, Any], *, retain: bool = False, absolute_topic: bool = False) -> None:
        if self._client is None:
            return
        full_topic = topic if absolute_topic else f"{self.config.mqtt_topic_prefix}/{topic.strip('/')}"
        try:
            self._client.publish(full_topic, json.dumps(payload, ensure_ascii=True), retain=retain)
        except Exception:
            LOGGER.exception("Failed to publish MQTT topic %s", full_topic)

    @staticmethod
    def _create_client() -> Any:
        if hasattr(mqtt, "CallbackAPIVersion"):
            return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="growatt-local-gateway")
        return mqtt.Client(client_id="growatt-local-gateway")

    def _on_connect(self, client: Any, userdata: Any, flags: Any, reason_code: Any, properties: Any = None) -> None:
        self.connected = True
        LOGGER.info("Connected to MQTT broker with result %s", reason_code)
        self.publish_discovery()

    def _on_disconnect(self, client: Any, userdata: Any, *args: Any) -> None:
        self.connected = False
        reason_code = args[-2] if len(args) >= 2 else args[-1] if args else "unknown"
        LOGGER.warning("Disconnected from MQTT broker with result %s", reason_code)
