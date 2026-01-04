# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# Tests for configuration generation methods

from unittest.mock import Mock

import yaml

from charm import CharmConfig, SungatherCharm


def mock_get_secret_not_found(label):
    """Mock get_secret that always raises SecretNotFoundError."""
    from ops import SecretNotFoundError

    raise SecretNotFoundError(label)


def test_generate_config_yaml_basic():
    """Test config.yaml generation with basic configuration."""
    # Arrange
    mock_charm = Mock(spec=SungatherCharm)
    mock_charm.model.get_secret = mock_get_secret_not_found

    charm_config = CharmConfig(
        inverter_host="192.168.1.100",
        inverter_port=502,
        connection_type="modbus",
        inverter_model=None,
        scan_interval=30,
        smart_meter=False,
        level=1,
        enable_webserver=True,
        webserver_port=8080,
        enable_mqtt=False,
        mqtt_host=None,
        mqtt_port=1883,
        mqtt_topic="sungather",
        mqtt_homeassistant=False,
        enable_influxdb=False,
        influxdb_host=None,
        influxdb_port=8086,
        influxdb_database="sungather",
        influxdb_version=2,
        pvoutput_enabled=False,
        log_level="INFO",
    )

    # Act
    config_yaml = SungatherCharm._generate_config_yaml(mock_charm, charm_config)
    config_dict = yaml.safe_load(config_yaml)

    # Assert
    assert config_dict["inverter"]["host"] == "192.168.1.100"
    assert config_dict["inverter"]["port"] == 502
    assert config_dict["inverter"]["connection"] == "modbus"
    assert config_dict["inverter"]["scan_interval"] == 30
    assert config_dict["inverter"]["level"] == 1
    assert config_dict["inverter"]["smart_meter"] is False

    # Check webserver export
    webserver_export = next((e for e in config_dict["exports"] if e["name"] == "webserver"), None)
    assert webserver_export is not None
    assert webserver_export["enabled"] is True
    assert webserver_export["port"] == 8080


def test_generate_config_yaml_with_mqtt():
    """Test config.yaml generation with MQTT enabled."""
    # Arrange
    mock_charm = Mock(spec=SungatherCharm)
    mock_charm.model.get_secret = mock_get_secret_not_found

    charm_config = CharmConfig(
        inverter_host="192.168.1.100",
        inverter_port=502,
        connection_type="modbus",
        inverter_model=None,
        scan_interval=30,
        smart_meter=False,
        level=1,
        enable_webserver=False,
        webserver_port=8080,
        enable_mqtt=True,
        mqtt_host="mqtt.example.com",
        mqtt_port=1883,
        mqtt_topic="solar/inverter",
        mqtt_homeassistant=True,
        enable_influxdb=False,
        influxdb_host=None,
        influxdb_port=8086,
        influxdb_database="sungather",
        influxdb_version=2,
        pvoutput_enabled=False,
        log_level="INFO",
    )

    # Act
    config_yaml = SungatherCharm._generate_config_yaml(mock_charm, charm_config)
    config_dict = yaml.safe_load(config_yaml)

    # Assert
    mqtt_export = next((e for e in config_dict["exports"] if e["name"] == "mqtt"), None)
    assert mqtt_export is not None
    assert mqtt_export["enabled"] is True
    assert mqtt_export["host"] == "mqtt.example.com"
    assert mqtt_export["port"] == 1883
    assert mqtt_export["topic"] == "solar/inverter"
    assert mqtt_export["homeassistant"] is True


def test_generate_config_yaml_with_influxdb():
    """Test config.yaml generation with InfluxDB enabled."""
    # Arrange
    mock_charm = Mock(spec=SungatherCharm)
    mock_charm.model.get_secret = mock_get_secret_not_found

    charm_config = CharmConfig(
        inverter_host="192.168.1.100",
        inverter_port=502,
        connection_type="modbus",
        inverter_model=None,
        scan_interval=30,
        smart_meter=False,
        level=1,
        enable_webserver=False,
        webserver_port=8080,
        enable_mqtt=False,
        mqtt_host=None,
        mqtt_port=1883,
        mqtt_topic="sungather",
        mqtt_homeassistant=False,
        enable_influxdb=True,
        influxdb_host="influxdb.example.com",
        influxdb_port=8086,
        influxdb_database="solar",
        influxdb_version=2,
        pvoutput_enabled=False,
        log_level="INFO",
    )

    # Act
    config_yaml = SungatherCharm._generate_config_yaml(mock_charm, charm_config)
    config_dict = yaml.safe_load(config_yaml)

    # Assert
    influxdb_export = next((e for e in config_dict["exports"] if e["name"] == "influxdb"), None)
    assert influxdb_export is not None
    assert influxdb_export["enabled"] is True
    assert influxdb_export["host"] == "influxdb.example.com"
    assert influxdb_export["port"] == 8086
    assert influxdb_export["database"] == "solar"
    assert influxdb_export["version"] == 2


def test_pebble_layer_generation():
    """Test that the Pebble layer is correctly generated."""
    # Arrange
    mock_charm = Mock(spec=SungatherCharm)

    charm_config = CharmConfig(
        inverter_host="192.168.1.100",
        inverter_port=502,
        connection_type="modbus",
        inverter_model=None,
        scan_interval=30,
        smart_meter=False,
        level=1,
        enable_webserver=True,
        webserver_port=8080,
        enable_mqtt=False,
        mqtt_host=None,
        mqtt_port=1883,
        mqtt_topic="sungather",
        mqtt_homeassistant=False,
        enable_influxdb=False,
        influxdb_host=None,
        influxdb_port=8086,
        influxdb_database="sungather",
        influxdb_version=2,
        pvoutput_enabled=False,
        log_level="INFO",
    )

    environment = SungatherCharm._get_environment(mock_charm, charm_config)

    # Act
    layer = SungatherCharm._build_pebble_layer(mock_charm, charm_config, environment)

    # Assert
    assert "sungather" in layer["services"]  # type: ignore[typeddict-item]
    service = layer["services"]["sungather"]  # type: ignore[typeddict-item]
    assert service["startup"] == "enabled"  # type: ignore[typeddict-item]
    assert "/usr/bin/python3.10" in service["command"]  # type: ignore[typeddict-item]
    assert "sungather.py" in service["command"]  # type: ignore[typeddict-item]
    assert "-c /config/config.yaml" in service["command"]  # type: ignore[typeddict-item]
    assert service["working-dir"] == "/opt/sungather/SunGather"  # type: ignore[typeddict-item]
    assert "TZ" in service["environment"]  # type: ignore[typeddict-item]
    assert "LOG_LEVEL" in service["environment"]  # type: ignore[typeddict-item]
    assert "PYTHONPATH" in service["environment"]  # type: ignore[typeddict-item]
    assert service["environment"]["PYTHONPATH"] == "/opt/sungather-lib"  # type: ignore[typeddict-item]


def test_environment_generation():
    """Test that environment variables are correctly generated."""
    # Arrange
    mock_charm = Mock(spec=SungatherCharm)

    charm_config = CharmConfig(
        inverter_host="192.168.1.100",
        inverter_port=502,
        connection_type="modbus",
        inverter_model=None,
        scan_interval=30,
        smart_meter=False,
        level=1,
        enable_webserver=True,
        webserver_port=8080,
        enable_mqtt=False,
        mqtt_host=None,
        mqtt_port=1883,
        mqtt_topic="sungather",
        mqtt_homeassistant=False,
        enable_influxdb=False,
        influxdb_host=None,
        influxdb_port=8086,
        influxdb_database="sungather",
        influxdb_version=2,
        pvoutput_enabled=False,
        log_level="DEBUG",
    )

    # Act
    environment = SungatherCharm._get_environment(mock_charm, charm_config)

    # Assert
    assert environment["TZ"] == "UTC"
    assert environment["LOG_LEVEL"] == "10"  # DEBUG level
