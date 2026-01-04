# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""Functions for interacting with the SunGather workload.

The intention is that this module could be used outside the context of a charm.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import ops

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def get_version(container: ops.Container) -> str | None:
    """Get the running version of SunGather.

    Args:
        container: The Pebble container running SunGather.

    Returns:
        The version string or None if unable to determine.
    """
    try:
        # Try to get version from the sungather package
        process = container.exec(
            ["/usr/bin/python3.10", "-c", "import sungather; print(sungather.__version__)"],
            timeout=5.0,
            encoding="utf-8",
            environment={"PYTHONPATH": "/opt/sungather-lib"},
        )
        stdout, _ = process.wait_output()
        return stdout.strip()
    except (ops.pebble.ExecError, AttributeError):
        logger.debug("Unable to determine SunGather version")
        return None


def get_inverter_info(container: ops.Container, config_path: str) -> dict[str, str]:
    """Get information about the connected inverter.

    Args:
        container: The Pebble container running SunGather.
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing inverter information.

    Raises:
        Exception: If unable to get inverter information.
    """
    try:
        # This would require SunGather to support a --get-info flag or similar
        # For now, return what we know
        return {
            "status": "Configuration loaded",
            "config-path": config_path,
            "message": "Inverter auto-detection happens on first data collection",
        }
    except Exception as e:
        logger.error("Failed to get inverter info: %s", e)
        raise


def test_connection(container: ops.Container, config_path: str) -> dict[str, str]:
    """Test the connection to the inverter.

    Args:
        container: The Pebble container running SunGather.
        config_path: Path to the configuration file.

    Returns:
        Dictionary containing test results.

    Raises:
        Exception: If connection test fails.
    """
    try:
        # Run sungather with --runonce to test the connection
        process = container.exec(
            [
                "/usr/bin/python3.10",
                "sungather.py",
                "-c",
                config_path,
                "--runonce",
            ],
            timeout=30.0,
            encoding="utf-8",
            working_dir="/opt/sungather/SunGather",
            environment={"PYTHONPATH": "/opt/sungather-lib"},
        )
        stdout, stderr = process.wait_output()

        # Check for common error patterns
        if "error" in stdout.lower() or (stderr and "error" in stderr.lower()):
            return {
                "status": "failed",
                "message": "Connection test failed - check logs for details",
                "output": stdout[:200],  # Truncate for readability
            }

        return {
            "status": "success",
            "message": "Successfully connected to inverter and collected data",
        }
    except ops.pebble.ExecError as e:
        logger.error("Connection test failed: %s", e)
        return {
            "status": "failed",
            "message": f"Connection test failed: {e}",
        }
