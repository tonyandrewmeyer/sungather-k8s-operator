# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""Sungrow inverter register map with realistic test data.

This module provides a simulated register map based on Sungrow's Communication Protocol
for PV Grid-Connected String Inverters. The registers contain realistic dummy data for
testing purposes.
"""

from __future__ import annotations

# Register addresses and their values
# Based on common Sungrow inverter register maps


class SungrowRegisters:
    """Simulates Sungrow inverter registers with realistic data."""

    def __init__(self, model: str = "SG5K-D") -> None:
        """Initialise the register map.

        Args:
            model: Inverter model identifier.
        """
        self.model = model
        self._registers: dict[int, int] = {}
        self._initialise_registers()

    def _initialise_registers(self) -> None:
        """Initialise registers with realistic values."""
        # Device information (holding registers 4999-5022)
        self._set_string_register(4999, self.model, 15)  # Device model
        self._set_string_register(5015, "V1.0.0", 7)  # Firmware version

        # Real-time data (input registers 5000-5200)
        # These are updated dynamically
        self._registers[5000] = 2500  # DC Voltage 1 (25.00V)
        self._registers[5001] = 150  # DC Current 1 (1.50A)
        self._registers[5002] = 2480  # DC Voltage 2 (24.80V)
        self._registers[5003] = 145  # DC Current 2 (1.45A)

        # AC output
        self._registers[5011] = 23000  # Phase A Voltage (230.00V)
        self._registers[5012] = 23050  # Phase B Voltage (230.50V)
        self._registers[5013] = 22980  # Phase C Voltage (229.80V)
        self._registers[5017] = 520  # Phase A Current (5.20A)
        self._registers[5018] = 515  # Phase B Current (5.15A)
        self._registers[5019] = 518  # Phase C Current (5.18A)

        # Power
        self._registers[5031] = 3500  # Total DC power (3500W)
        self._registers[5032] = 0
        self._registers[5033] = 3450  # Total active power (3450W)
        self._registers[5034] = 0

        # Energy
        self._registers[5003] = 15000  # Total energy (1500.0 kWh) - low word
        self._registers[5004] = 0  # Total energy - high word
        self._registers[5035] = 125  # Daily energy (12.5 kWh)

        # Temperature and status
        self._registers[5007] = 450  # Internal temperature (45.0°C)
        self._registers[5008] = 1  # Running status (1 = Running)
        self._registers[5009] = 0  # Fault code (0 = No fault)

        # Inverter efficiency
        self._registers[5036] = 9850  # Efficiency (98.50%)

        # Grid frequency
        self._registers[5035] = 5000  # Grid frequency (50.00 Hz)

    def _set_string_register(self, start_addr: int, value: str, max_length: int) -> None:
        """Set a string value across multiple registers.

        Args:
            start_addr: Starting register address.
            value: String value to store.
            max_length: Maximum string length in characters.
        """
        # Pad or truncate string
        value = value.ljust(max_length)[:max_length]

        # Store as pairs of characters in 16-bit registers
        for i in range(0, len(value), 2):
            if i + 1 < len(value):
                reg_value = (ord(value[i]) << 8) | ord(value[i + 1])
            else:
                reg_value = ord(value[i]) << 8
            self._registers[start_addr + i // 2] = reg_value

    def read_holding_registers(self, address: int, count: int) -> list[int]:
        """Read holding registers.

        Args:
            address: Starting register address.
            count: Number of registers to read.

        Returns:
            List of register values.
        """
        values = []
        for addr in range(address, address + count):
            values.append(self._registers.get(addr, 0))
        return values

    def read_input_registers(self, address: int, count: int) -> list[int]:
        """Read input registers.

        Args:
            address: Starting register address.
            count: Number of registers to read.

        Returns:
            List of register values.
        """
        # Update dynamic values before reading
        self._update_dynamic_registers()

        values = []
        for addr in range(address, address + count):
            values.append(self._registers.get(addr, 0))
        return values

    def _update_dynamic_registers(self) -> None:
        """Update registers that change over time (for realistic simulation)."""
        # Simulate slight variations in power output
        import random

        base_power = 3500
        variation = random.randint(-50, 50)
        self._registers[5033] = base_power + variation  # Active power

        # Update daily energy (incrementing slowly)
        current_daily = self._registers.get(5035, 0)
        self._registers[5035] = min(current_daily + 1, 30000)  # Cap at 3000 kWh daily

    def write_holding_register(self, address: int, value: int) -> None:
        """Write to a holding register.

        Args:
            address: Register address.
            value: Value to write.
        """
        # Only allow writes to certain registers (configuration)
        if 4000 <= address < 5000:
            self._registers[address] = value
