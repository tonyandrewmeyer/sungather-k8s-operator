# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""Main mock Sungrow server orchestrator.

This module provides a unified interface to start both Modbus TCP and HTTP servers
for testing the SunGather charm with different connection types.
"""

from __future__ import annotations

import logging
import time
from typing import Literal

from mock_sungrow.http_server import HTTPModbusServer
from mock_sungrow.modbus_server import ModbusTCPServer
from mock_sungrow.registers import SungrowRegisters

logger = logging.getLogger(__name__)

ServerType = Literal["modbus", "http", "both"]


class MockSungrowServer:
    """Orchestrates mock Sungrow inverter servers for integration testing."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        modbus_port: int = 5020,
        http_port: int = 8082,
        model: str = "SG5K-D",
        server_type: ServerType = "both",
    ) -> None:
        """Initialise the mock Sungrow server.

        Args:
            host: Host address to bind to.
            modbus_port: Port for Modbus TCP server.
            http_port: Port for HTTP server.
            model: Inverter model to simulate.
            server_type: Which servers to run ('modbus', 'http', or 'both').
        """
        self.host = host
        self.modbus_port = modbus_port
        self.http_port = http_port
        self.model = model
        self.server_type = server_type

        # Shared register map
        self.registers = SungrowRegisters(model=model)

        # Servers
        self._modbus_server: ModbusTCPServer | None = None
        self._http_server: HTTPModbusServer | None = None

    def start(self) -> None:
        """Start the mock servers."""
        logger.info(f"Starting mock Sungrow server ({self.server_type}) for model {self.model}")

        if self.server_type in ("modbus", "both"):
            self._modbus_server = ModbusTCPServer(
                host=self.host,
                port=self.modbus_port,
                registers=self.registers,
            )
            self._modbus_server.start()

        if self.server_type in ("http", "both"):
            self._http_server = HTTPModbusServer(
                host=self.host,
                port=self.http_port,
                registers=self.registers,
            )
            self._http_server.start()

        # Give servers time to start
        time.sleep(0.5)

        logger.info(
            f"Mock Sungrow server ready - Modbus: {self.host}:{self.modbus_port}, "
            f"HTTP: {self.host}:{self.http_port}"
        )

    def stop(self) -> None:
        """Stop all mock servers."""
        logger.info("Stopping mock Sungrow server")

        if self._modbus_server:
            self._modbus_server.stop()
            self._modbus_server = None

        if self._http_server:
            self._http_server.stop()
            self._http_server = None

        logger.info("Mock Sungrow server stopped")

    def is_running(self) -> bool:
        """Check if servers are running.

        Returns:
            True if any server is running, False otherwise.
        """
        modbus_running = self._modbus_server.is_running() if self._modbus_server else False
        http_running = self._http_server.is_running() if self._http_server else False
        return modbus_running or http_running

    def get_connection_info(self, connection_type: str = "modbus") -> dict[str, str | int]:
        """Get connection information for the specified type.

        Args:
            connection_type: Connection type ('modbus' or 'http').

        Returns:
            Dictionary with host and port information.
        """
        if connection_type == "modbus":
            return {
                "host": self.host,
                "port": self.modbus_port,
                "connection-type": "modbus",
            }
        elif connection_type == "http":
            return {
                "host": self.host,
                "port": self.http_port,
                "connection-type": "http",
            }
        else:
            raise ValueError(f"Unknown connection type: {connection_type}")


# Convenience functions for pytest fixtures


def start_mock_server(
    host: str = "127.0.0.1",
    modbus_port: int = 5020,
    http_port: int = 8082,
    model: str = "SG5K-D",
    server_type: ServerType = "both",
) -> MockSungrowServer:
    """Start a mock Sungrow server.

    Args:
        host: Host address to bind to.
        modbus_port: Port for Modbus TCP server.
        http_port: Port for HTTP server.
        model: Inverter model to simulate.
        server_type: Which servers to run.

    Returns:
        Running MockSungrowServer instance.
    """
    server = MockSungrowServer(
        host=host,
        modbus_port=modbus_port,
        http_port=http_port,
        model=model,
        server_type=server_type,
    )
    server.start()
    return server
