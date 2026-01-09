# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# Integration tests using the mock Sungrow server.
# These tests verify that the charm works correctly with a functioning workload.
#
# IMPORTANT: These tests require a working OCI image with all dependencies.
# The default image (bohdans/sungather:latest) is broken and will not work.
#
# To run these tests successfully:
# 1. Build the working rock: cd rock && rockcraft pack
# 2. Load it into the registry:
#    rockcraft.skopeo copy oci-archive:sungather_0.3.8_amd64.rock \
#      docker-daemon:sungather:0.3.8
# 3. Push to a registry accessible from your K8s cluster
# 4. Update the METADATA below to use your working image
#
# These tests are currently expected to fail with the default broken image.
# They demonstrate the test infrastructure and mock server functionality.

import logging
import pathlib

import jubilant
import pytest
import yaml

logger = logging.getLogger(__name__)

METADATA = yaml.safe_load(pathlib.Path("charmcraft.yaml").read_text())

# Mark all tests in this module as requiring a working image
pytestmark = pytest.mark.skip(
    reason="Requires working OCI image - default bohdans/sungather:latest is broken. "
    "Build the rock in rock/ directory and update test to use it."
)


def test_deploy_with_mock_modbus_server(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Deploy the charm with mock Modbus server and verify it reaches active status."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    # Get connection info for Modbus
    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
        "scan-interval": 60,
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )

    # Wait for the charm to reach active status
    # With the mock server, the workload should start successfully
    juju.wait(jubilant.all_active, timeout=180)

    status = juju.status()
    unit_status = status.apps["sungather"].units["sungather/0"].workload_status.current
    assert unit_status == "active"


def test_deploy_with_mock_http_server(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Deploy the charm with mock HTTP server and verify it reaches active status."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    # Get connection info for HTTP
    conn_info = mock_sungrow.get_connection_info("http")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "http",
        "scan-interval": 60,
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )

    # Wait for the charm to reach active status
    juju.wait(jubilant.all_active, timeout=180)

    status = juju.status()
    unit_status = status.apps["sungather"].units["sungather/0"].workload_status.current
    assert unit_status == "active"


def test_run_once_action_with_mock(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Test the run-once action with a working mock server."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )
    juju.wait(jubilant.all_active, timeout=180)

    # Run the action - should now succeed with mock server
    result = juju.run("sungather/0", "run-once")

    # The action should complete successfully
    assert result.status == "completed"


def test_test_connection_action_with_mock(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Test the test-connection action with a working mock server."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )
    juju.wait(jubilant.all_active, timeout=180)

    # Run the test-connection action
    result = juju.run("sungather/0", "test-connection")

    # The action should complete successfully
    assert result.status == "completed"
    assert "status" in result.results
    # With a working mock server, connection should succeed
    assert result.results.get("status") == "success"


def test_get_inverter_info_action_with_mock(
    charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow
):
    """Test the get-inverter-info action with a working mock server."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )
    juju.wait(jubilant.all_active, timeout=180)

    # Run the action
    result = juju.run("sungather/0", "get-inverter-info")

    # The action should complete
    assert result.status == "completed"
    assert "status" in result.results or "config-path" in result.results


def test_mqtt_config_with_mock(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Test MQTT configuration with mock server."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
        "enable-mqtt": True,
        "mqtt-host": "mqtt.example.com",
        "mqtt-topic": "solar/inverter",
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )
    # With mock server, should reach active status even with MQTT configured
    juju.wait(jubilant.all_active, timeout=180)

    status = juju.status()
    unit_status = status.apps["sungather"].units["sungather/0"].workload_status.current
    assert unit_status == "active"


def test_webserver_enabled_with_mock(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Test that the webserver is enabled and charm reaches active status."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
        "enable-webserver": True,
        "webserver-port": 8080,
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )
    juju.wait(jubilant.all_active, timeout=180)

    status = juju.status()
    unit_status = status.apps["sungather"].units["sungather/0"].workload_status.current
    assert unit_status == "active"


def test_config_change_with_mock(charm: pathlib.Path, juju: jubilant.Juju, mock_sungrow):
    """Test that configuration changes work correctly with mock server."""
    resources = {"sungather-image": METADATA["resources"]["sungather-image"]["upstream-source"]}

    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
        "scan-interval": 30,
    }

    juju.deploy(
        charm.resolve(),
        app="sungather",
        resources=resources,
        config=config,
    )
    juju.wait(jubilant.all_active, timeout=180)

    # Update configuration
    juju.config("sungather", {"scan-interval": "60"})
    juju.wait(jubilant.all_agents_idle, timeout=120)

    # Should still be active after config change
    status = juju.status()
    unit_status = status.apps["sungather"].units["sungather/0"].workload_status.current
    assert unit_status == "active"
