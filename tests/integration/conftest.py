# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# The integration tests use the Jubilant library. See https://documentation.ubuntu.com/jubilant/
# To learn more about testing, see https://documentation.ubuntu.com/ops/latest/explanation/testing/

import logging
import os
import pathlib
import sys
import time

import jubilant
import pytest
from mock_sungrow.server import MockSungrowServer

logger = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def juju(request: pytest.FixtureRequest):
    """Create a temporary Juju model for running tests."""
    with jubilant.temp_model() as juju:
        yield juju

        if request.session.testsfailed:
            logger.info("Collecting Juju logs...")
            time.sleep(0.5)  # Wait for Juju to process logs.
            log = juju.debug_log(limit=1000)
            print(log, end="", file=sys.stderr)


@pytest.fixture(scope="session")
def charm():
    """Return the path of the charm under test."""
    if "CHARM_PATH" in os.environ:
        charm_path = pathlib.Path(os.environ["CHARM_PATH"])
        if not charm_path.exists():
            raise FileNotFoundError(f"Charm does not exist: {charm_path}")
        return charm_path
    # Modify below if you're building for multiple bases or architectures.
    charm_paths = list(pathlib.Path(".").glob("*.charm"))
    if not charm_paths:
        raise FileNotFoundError("No .charm file in current directory")
    if len(charm_paths) > 1:
        path_list = ", ".join(str(path) for path in charm_paths)
        raise ValueError(f"More than one .charm file in current directory: {path_list}")
    return charm_paths[0]


@pytest.fixture(scope="module")
def mock_sungrow():
    """Start a mock Sungrow inverter server for testing.

    This fixture starts both Modbus TCP and HTTP servers that simulate a Sungrow
    inverter. Tests can use this to verify charm behaviour with a working workload.

    The servers bind to 0.0.0.0 to be accessible from Kubernetes pods.
    Connection info uses the host's IP address.

    The servers run on non-privileged ports:
    - Modbus TCP: 5020 (instead of standard 502)
    - HTTP: 8082 (standard WiNet-S port)

    Returns:
        MockSungrowServer instance with connection info methods.
    """
    import socket

    # Get host IP that's accessible from K8s pods
    hostname = socket.gethostname()
    host_ip = socket.gethostbyname(hostname)

    logger.info(f"Starting mock Sungrow inverter server on {host_ip}")
    # Bind to 0.0.0.0 so it's accessible from Kubernetes pods
    server = MockSungrowServer(
        host="0.0.0.0",
        modbus_port=5020,
        http_port=8082,
        model="SG5K-D",
        server_type="both",
    )
    server.start()

    # Override host for connection info to use the reachable IP
    server.host = host_ip

    yield server

    logger.info("Stopping mock Sungrow inverter server")
    server.stop()
