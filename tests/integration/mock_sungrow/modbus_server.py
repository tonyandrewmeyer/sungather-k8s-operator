# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""Modbus TCP server implementation for mock Sungrow inverter."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

import pymodbus
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.datastore.context import ModbusDeviceContext
from pymodbus.server import StartTcpServer

if TYPE_CHECKING:
    from mock_sungrow.registers import SungrowRegisters

logger = logging.getLogger(__name__)


class SungrowModbusDataBlock(ModbusSequentialDataBlock):
    """Custom data block that delegates to SungrowRegisters."""

    def __init__(self, registers: SungrowRegisters, register_type: str) -> None:
        """Initialise the data block.

        Args:
            registers: SungrowRegisters instance.
            register_type: Type of registers ('holding' or 'input').
        """
        self._sungrow_registers = registers
        self._register_type = register_type
        # Initialise with dummy values - we override getValues/setValues
        super().__init__(0, [0] * 65536)

    def getValues(self, address: int, count: int = 1) -> list[int]:
        """Read values from the register map.

        Args:
            address: Starting address.
            count: Number of values to read.

        Returns:
            List of register values.
        """
        if self._register_type == "holding":
            return self._sungrow_registers.read_holding_registers(address, count)
        elif self._register_type == "input":
            return self._sungrow_registers.read_input_registers(address, count)
        return [0] * count

    def setValues(self, address: int, values: list[int]) -> None:
        """Write values to the register map.

        Args:
            address: Starting address.
            values: Values to write.
        """
        if self._register_type == "holding":
            for i, value in enumerate(values):
                self._sungrow_registers.write_holding_register(address + i, value)


class ModbusTCPServer:
    """Modbus TCP server for simulating a Sungrow inverter."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 5020, registers: SungrowRegisters | None = None
    ) -> None:
        """Initialise the Modbus TCP server.

        Args:
            host: Host address to bind to.
            port: Port to listen on.
            registers: SungrowRegisters instance (created if not provided).
        """
        self.host = host
        self.port = port
        self.registers = registers if registers else self._create_default_registers()
        self._server_thread: threading.Thread | None = None
        self._running = False

    def _create_default_registers(self) -> SungrowRegisters:
        """Create default registers.

        Returns:
            SungrowRegisters instance.
        """
        from mock_sungrow.registers import SungrowRegisters

        return SungrowRegisters(model="SG5K-D")

    def start(self) -> None:
        """Start the Modbus TCP server in a background thread."""
        if self._running:
            logger.warning("Modbus server already running")
            return

        # Create data blocks
        holding_block = SungrowModbusDataBlock(self.registers, "holding")
        input_block = SungrowModbusDataBlock(self.registers, "input")

        # Create device context (replaces slave context in pymodbus 3.x)
        device_context = ModbusDeviceContext(
            di=ModbusSequentialDataBlock(0, [0] * 100),  # Discrete Inputs
            co=ModbusSequentialDataBlock(0, [0] * 100),  # Coils
            hr=holding_block,  # Holding Registers
            ir=input_block,  # Input Registers
        )

        # Create server context
        context = ModbusServerContext(devices={1: device_context}, single=True)

        # Create device identification
        identity = pymodbus.ModbusDeviceIdentification()
        identity.VendorName = "Sungrow"
        identity.ProductCode = self.registers.model
        identity.VendorUrl = "https://www.sungrowpower.com"
        identity.ProductName = "Mock Sungrow Inverter"
        identity.ModelName = self.registers.model
        identity.MajorMinorRevision = pymodbus.__version__

        # Start server in thread
        self._running = True
        self._server_thread = threading.Thread(
            target=self._run_server,
            args=(context, identity),
            daemon=True,
        )
        self._server_thread.start()
        logger.info(f"Modbus TCP server started on {self.host}:{self.port}")

    def _run_server(
        self, context: ModbusServerContext, identity: pymodbus.ModbusDeviceIdentification
    ) -> None:
        """Run the Modbus server.

        Args:
            context: Server context.
            identity: Device identification.
        """
        try:
            StartTcpServer(
                context=context,
                identity=identity,
                address=(self.host, self.port),
            )
        except Exception as e:
            logger.error(f"Modbus server error: {e}")
            self._running = False

    def stop(self) -> None:
        """Stop the Modbus TCP server."""
        if not self._running:
            return

        self._running = False
        if self._server_thread and self._server_thread.is_alive():
            # Note: pymodbus doesn't provide a clean shutdown mechanism
            # The thread will terminate when the process exits
            logger.info("Modbus TCP server stopped")

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running
