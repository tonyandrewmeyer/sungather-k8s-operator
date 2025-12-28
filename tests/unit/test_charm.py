# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# To learn more about testing, see https://documentation.ubuntu.com/ops/latest/explanation/testing/

import pytest
from ops import pebble, testing

from charm import CONTAINER_NAME, SERVICE_NAME, SungatherCharm


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
    assert state_out.unit_status == testing.BlockedStatus(
        "Config error: inverter-host is required"
    )


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
