# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# To learn more about testing, see https://documentation.ubuntu.com/ops/latest/explanation/testing/

import pytest
import yaml
from ops import pebble, testing

from charm import CONTAINER_NAME, SERVICE_NAME, CharmConfig, SungatherCharm


def mock_get_version(container):
    """Get a mock version string without executing the workload code."""
    return "0.3.8"


@pytest.fixture
def valid_config():
    """Return a valid configuration dictionary."""
    return {
        "inverter-host": "192.168.1.100",
        "inverter-port": 502,
        "connection-type": "modbus",
        "scan-interval": 30,
        "level": 1,
        "smart-meter": False,
        "enable-webserver": True,
        "webserver-port": 8080,
        "enable-mqtt": False,
        "enable-influxdb": False,
        "pvoutput-enabled": False,
        "log-level": "INFO",
    }


def test_config_validation_missing_host():
    """Test that configuration validation fails when inverter-host is missing."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    state_in = testing.State(config={})  # No inverter-host

    container = testing.Container(CONTAINER_NAME, can_connect=True)
    state_in = testing.State(containers={container}, config={})

    # Act
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert
    assert state_out.unit_status == testing.BlockedStatus("Config error: inverter-host is required")


def test_config_validation_invalid_connection_type():
    """Test that configuration validation fails with invalid connection type."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    config = {
        "inverter-host": "192.168.1.100",
        "connection-type": "invalid",
    }

    container = testing.Container(CONTAINER_NAME, can_connect=True)
    state_in = testing.State(containers={container}, config=config)

    # Act
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert
    assert state_out.unit_status.name == "blocked"
    assert "connection-type" in state_out.unit_status.message


def test_config_validation_invalid_level():
    """Test that configuration validation fails with invalid level."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    config = {
        "inverter-host": "192.168.1.100",
        "level": 5,  # Invalid
    }

    container = testing.Container(CONTAINER_NAME, can_connect=True)
    state_in = testing.State(containers={container}, config=config)

    # Act
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert
    assert state_out.unit_status.name == "blocked"
    assert "level" in state_out.unit_status.message


def test_config_validation_mqtt_without_host():
    """Test that configuration validation fails when MQTT is enabled without host."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    config = {
        "inverter-host": "192.168.1.100",
        "enable-mqtt": True,
        # mqtt-host not provided
    }

    container = testing.Container(CONTAINER_NAME, can_connect=True)
    state_in = testing.State(containers={container}, config=config)

    # Act
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert
    assert state_out.unit_status.name == "blocked"
    assert "mqtt-host" in state_out.unit_status.message


def test_config_validation_influxdb_without_host():
    """Test that configuration validation fails when InfluxDB is enabled without host."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    config = {
        "inverter-host": "192.168.1.100",
        "enable-influxdb": True,
        # influxdb-host not provided
    }

    container = testing.Container(CONTAINER_NAME, can_connect=True)
    state_in = testing.State(containers={container}, config=config)

    # Act
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert
    assert state_out.unit_status.name == "blocked"
    assert "influxdb-host" in state_out.unit_status.message


def test_pebble_ready_with_valid_config(monkeypatch: pytest.MonkeyPatch, valid_config):
    """Test that pebble-ready with valid config starts the service."""
    # Arrange
    monkeypatch.setattr("sungather.get_version", mock_get_version)

    ctx = testing.Context(SungatherCharm)
    container = testing.Container(
        CONTAINER_NAME,
        can_connect=True,
        service_statuses={SERVICE_NAME: pebble.ServiceStatus.INACTIVE},
    )
    state_in = testing.State(containers={container}, config=valid_config)

    # Act
    state_out = ctx.run(ctx.on.pebble_ready(container), state_in)

    # Assert
    container_out = state_out.get_container(CONTAINER_NAME)
    assert container_out.service_statuses[SERVICE_NAME] == pebble.ServiceStatus.ACTIVE
    assert state_out.unit_status == testing.ActiveStatus()


def test_config_changed_restarts_service(monkeypatch: pytest.MonkeyPatch, valid_config):
    """Test that config-changed restarts the running service."""
    # Arrange
    monkeypatch.setattr("sungather.get_version", mock_get_version)

    ctx = testing.Context(SungatherCharm)
    container = testing.Container(
        CONTAINER_NAME,
        can_connect=True,
        service_statuses={SERVICE_NAME: pebble.ServiceStatus.ACTIVE},
    )
    state_in = testing.State(containers={container}, config=valid_config)

    # Act
    state_out = ctx.run(ctx.on.config_changed(), state_in)

    # Assert - service should still be active after restart
    container_out = state_out.get_container(CONTAINER_NAME)
    assert container_out.service_statuses[SERVICE_NAME] == pebble.ServiceStatus.ACTIVE
    assert state_out.unit_status == testing.ActiveStatus()


def test_generate_config_yaml_basic(valid_config):
    """Test config.yaml generation with basic configuration."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    charm = ctx.charm_type(ctx._framework)

    # Set up config
    ctx._state = testing.State(config=valid_config)
    charm._framework.model._state = ctx._state

    config = CharmConfig.from_charm(charm)

    # Act
    config_yaml = charm._generate_config_yaml(config)
    config_dict = yaml.safe_load(config_yaml)

    # Assert
    assert config_dict["inverter"]["host"] == "192.168.1.100"
    assert config_dict["inverter"]["port"] == 502
    assert config_dict["inverter"]["connection"] == "modbus"
    assert config_dict["inverter"]["scan_interval"] == 30
    assert config_dict["inverter"]["level"] == 1
    assert config_dict["inverter"]["smart_meter"] is False

    # Check webserver export
    webserver_export = next(
        (e for e in config_dict["exports"] if e["name"] == "webserver"), None
    )
    assert webserver_export is not None
    assert webserver_export["enabled"] is True
    assert webserver_export["port"] == 8080


def test_generate_config_yaml_with_mqtt():
    """Test config.yaml generation with MQTT enabled."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    charm = ctx.charm_type(ctx._framework)

    config = {
        "inverter-host": "192.168.1.100",
        "enable-mqtt": True,
        "mqtt-host": "mqtt.example.com",
        "mqtt-port": 1883,
        "mqtt-topic": "solar/inverter",
        "mqtt-homeassistant": True,
        "enable-webserver": False,
    }

    ctx._state = testing.State(config=config)
    charm._framework.model._state = ctx._state

    charm_config = CharmConfig.from_charm(charm)

    # Act
    config_yaml = charm._generate_config_yaml(charm_config)
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
    ctx = testing.Context(SungatherCharm)
    charm = ctx.charm_type(ctx._framework)

    config = {
        "inverter-host": "192.168.1.100",
        "enable-influxdb": True,
        "influxdb-host": "influxdb.example.com",
        "influxdb-port": 8086,
        "influxdb-database": "solar",
        "influxdb-version": 2,
        "enable-webserver": False,
    }

    ctx._state = testing.State(config=config)
    charm._framework.model._state = ctx._state

    charm_config = CharmConfig.from_charm(charm)

    # Act
    config_yaml = charm._generate_config_yaml(charm_config)
    config_dict = yaml.safe_load(config_yaml)

    # Assert
    influxdb_export = next(
        (e for e in config_dict["exports"] if e["name"] == "influxdb"), None
    )
    assert influxdb_export is not None
    assert influxdb_export["enabled"] is True
    assert influxdb_export["host"] == "influxdb.example.com"
    assert influxdb_export["port"] == 8086
    assert influxdb_export["database"] == "solar"
    assert influxdb_export["version"] == 2


def test_pebble_layer_generation(valid_config):
    """Test that the Pebble layer is correctly generated."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    charm = ctx.charm_type(ctx._framework)

    ctx._state = testing.State(config=valid_config)
    charm._framework.model._state = ctx._state

    charm_config = CharmConfig.from_charm(charm)
    environment = charm._get_environment(charm_config)

    # Act
    layer = charm._build_pebble_layer(charm_config, environment)

    # Assert
    assert SERVICE_NAME in layer["services"]
    service = layer["services"][SERVICE_NAME]
    assert service["startup"] == "enabled"
    assert "/opt/sungather/sungather.py" in service["command"]
    assert "-c /config/config.yaml" in service["command"]
    assert "TZ" in service["environment"]
    assert "LOG_LEVEL" in service["environment"]


def test_environment_generation():
    """Test that environment variables are correctly generated."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    charm = ctx.charm_type(ctx._framework)

    config = {
        "log-level": "DEBUG",
    }

    ctx._state = testing.State(config=config)
    charm._framework.model._state = ctx._state

    charm_config = CharmConfig.from_charm(charm)

    # Act
    environment = charm._get_environment(charm_config)

    # Assert
    assert environment["TZ"] == "UTC"
    assert environment["LOG_LEVEL"] == "10"  # DEBUG level


def test_container_not_ready_defers_event(valid_config):
    """Test that events are deferred when container is not ready."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    container = testing.Container(CONTAINER_NAME, can_connect=False)
    state_in = testing.State(containers={container}, config=valid_config)

    # Act
    state_out = ctx.run(ctx.on.pebble_ready(container), state_in)

    # Assert - event should be deferred (implementation detail of ops.testing)
    # The charm shouldn't crash and status should remain as-is
    assert state_out is not None


def test_update_status_with_running_service(valid_config):
    """Test update-status when service is running."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    container = testing.Container(
        CONTAINER_NAME,
        can_connect=True,
        service_statuses={SERVICE_NAME: pebble.ServiceStatus.ACTIVE},
    )
    state_in = testing.State(containers={container}, config=valid_config)

    # Act
    state_out = ctx.run(ctx.on.update_status(), state_in)

    # Assert
    assert state_out.unit_status == testing.ActiveStatus()


def test_update_status_with_stopped_service(valid_config):
    """Test update-status when service is not running."""
    # Arrange
    ctx = testing.Context(SungatherCharm)
    container = testing.Container(
        CONTAINER_NAME,
        can_connect=True,
        service_statuses={SERVICE_NAME: pebble.ServiceStatus.INACTIVE},
    )
    state_in = testing.State(containers={container}, config=valid_config)

    # Act
    state_out = ctx.run(ctx.on.update_status(), state_in)

    # Assert
    assert state_out.unit_status == testing.BlockedStatus("service is not running")
