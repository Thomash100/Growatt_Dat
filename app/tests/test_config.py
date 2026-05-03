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
            "UI_LANGUAGE": "en",
            "METER_PROVIDER": "shelly_3em",
            "METER_POWER_SIGN": "inverted",
            "SHELLY_3EM_BASE_URL": "http://192.168.178.252",
            "SHELLY_3EM_GENERATION": "gen1",
            "SHELLY_3EM_TIMEOUT_SECONDS": "2.5",
            "UPDATE_CHECK_ENABLED": "false",
            "UPDATE_REPOSITORY": "Example/Repo",
            "UPDATE_CHECK_TIMEOUT_SECONDS": "6.5",
            "INTEGRATION_SCAN_DEFAULT_CIDR": "192.168.1.0/24",
            "INTEGRATION_SCAN_TIMEOUT_SECONDS": "0.8",
            "INTEGRATION_SCAN_CONCURRENCY": "16",
            "INTEGRATION_SCAN_MAX_HOSTS": "128",
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
    assert config.meter_provider == "shelly_3em"
    assert config.meter_power_sign == "inverted"
    assert config.shelly_3em_base_url == "http://192.168.178.252"
    assert config.shelly_3em_generation == "gen1"
    assert config.shelly_3em_timeout_seconds == 2.5
    assert config.update_check_enabled is False
    assert config.update_repository == "Example/Repo"
    assert config.update_check_timeout_seconds == 6.5
    assert config.integration_scan_default_cidr == "192.168.1.0/24"
    assert config.integration_scan_timeout_seconds == 0.8
    assert config.integration_scan_concurrency == 16
    assert config.integration_scan_max_hosts == 128
    assert config.control.ui_language == "en"
    assert config.control.zero_export_enabled is False
    assert config.control.target_grid_power_w == 40
    assert config.control.max_output_power_w == 700
    assert config.control.min_soc_percent == 20


def test_config_rejects_invalid_ui_language():
    try:
        AppConfig.from_env({"UI_LANGUAGE": "fr"}, load_dotenv=False)
    except ValueError as exc:
        assert "ui_language" in str(exc)
    else:
        raise AssertionError("Expected invalid UI language to raise ValueError")


def test_config_requires_shelly_base_url_for_shelly_provider():
    try:
        AppConfig.from_env(
            {"METER_PROVIDER": "shelly_3em", "SHELLY_3EM_BASE_URL": ""},
            load_dotenv=False,
    )
    except ValueError as exc:
        assert "shelly_3em_base_url" in str(exc)
    else:
        raise AssertionError("Expected missing Shelly base URL to raise ValueError")
