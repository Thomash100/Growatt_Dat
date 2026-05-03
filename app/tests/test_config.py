from app.config import AppConfig


def test_config_loads_from_environment_mapping():
    config = AppConfig.from_env(
        {
            "MQTT_HOST": "mosquitto.local",
            "MQTT_PORT": "1884",
            "MQTT_USERNAME": "example-user",
            "MQTT_PASSWORD": "example-password",
            "MQTT_TOPIC_PREFIX": "custom_prefix",
            "MQTT_DISCOVERY_PREFIX": "homeassistant",
            "DATABASE_PATH": "/tmp/gateway.sqlite",
            "WEB_PORT": "8090",
            "ZERO_EXPORT_ENABLED": "false",
            "TARGET_GRID_POWER_W": "40",
            "GRID_POWER_BAND_MIN_W": "25",
            "GRID_POWER_BAND_MAX_W": "90",
            "CONTROL_INTERVAL_SECONDS": "7",
            "MIN_OUTPUT_CHANGE_W": "35",
            "OUTPUT_STEP_W": "55",
            "MAX_OUTPUT_POWER_W": "700",
            "MIN_OUTPUT_POWER_W": "10",
            "MIN_SOC_PERCENT": "20",
            "STALE_MEASUREMENT_SECONDS": "12",
        },
        load_dotenv=False,
    )

    assert config.mqtt_host == "mosquitto.local"
    assert config.mqtt_port == 1884
    assert config.mqtt_username == "example-user"
    assert config.mqtt_password == "example-password"
    assert config.web_port == 8090
    assert config.control.zero_export_enabled is False
    assert config.control.target_grid_power_w == 40
    assert config.control.max_output_power_w == 700
    assert config.control.min_soc_percent == 20

