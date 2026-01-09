# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""HTTP/WebSocket server implementation for mock Sungrow inverter.

This implements the WiNet-S protocol which wraps Modbus RTU packets in HTTP/WebSocket.
"""

from __future__ import annotations

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mock_sungrow.registers import SungrowRegisters

logger = logging.getLogger(__name__)


class ModbusHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler that wraps Modbus RTU packets."""

    registers: SungrowRegisters  # Set by server

    def log_message(self, format: str, *args) -> None:
        """Override to use our logger."""
        logger.debug(f"{self.address_string()} - {format % args}")

    def do_POST(self) -> None:
        """Handle POST requests for Modbus RTU over HTTP."""
        if self.path == "/device/getParam":
            self._handle_modbus_request()
        else:
            self.send_error(404, "Not Found")

    def _handle_modbus_request(self) -> None:
        """Handle a Modbus RTU request wrapped in HTTP."""
        try:
            # Read the request body
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Parse JSON request
            request_data = json.loads(body.decode("utf-8"))

            # Extract Modbus parameters
            # Expected format: {"param": "MODBUS_RTU", "data": "base64_encoded_modbus_packet"}
            if request_data.get("param") == "MODBUS_RTU":
                # For simplicity, we'll support a simplified protocol
                # In real WiNet-S, this would be base64-encoded Modbus RTU packets
                slave_id = request_data.get("slave", 1)
                function_code = request_data.get("function", 3)  # Read holding registers
                start_addr = request_data.get("address", 5000)
                count = request_data.get("count", 10)

                # Read registers
                if function_code == 3:  # Read holding registers
                    values = self.registers.read_holding_registers(start_addr, count)
                elif function_code == 4:  # Read input registers
                    values = self.registers.read_input_registers(start_addr, count)
                else:
                    self.send_error(400, "Unsupported function code")
                    return

                # Build response
                response_data = {
                    "result": "success",
                    "slave": slave_id,
                    "function": function_code,
                    "address": start_addr,
                    "count": count,
                    "values": values,
                }

                # Send response
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode("utf-8"))
            else:
                self.send_error(400, "Invalid param")
        except Exception as e:
            logger.error(f"Error handling Modbus HTTP request: {e}")
            self.send_error(500, "Internal Server Error")


class HTTPModbusServer:
    """HTTP server that wraps Modbus RTU packets for WiNet-S simulation."""

    def __init__(
        self, host: str = "127.0.0.1", port: int = 8082, registers: SungrowRegisters | None = None
    ) -> None:
        """Initialise the HTTP Modbus server.

        Args:
            host: Host address to bind to.
            port: Port to listen on.
            registers: SungrowRegisters instance (created if not provided).
        """
        self.host = host
        self.port = port
        self.registers = registers if registers else self._create_default_registers()
        self._server: HTTPServer | None = None
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
        """Start the HTTP server in a background thread."""
        if self._running:
            logger.warning("HTTP server already running")
            return

        # Create server with custom handler
        self._server = HTTPServer((self.host, self.port), ModbusHTTPHandler)
        # Set registers on handler class
        ModbusHTTPHandler.registers = self.registers

        self._running = True
        self._server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
        )
        self._server_thread.start()
        logger.info(f"HTTP Modbus server started on {self.host}:{self.port}")

    def _run_server(self) -> None:
        """Run the HTTP server."""
        if self._server:
            try:
                self._server.serve_forever()
            except Exception as e:
                logger.error(f"HTTP server error: {e}")
                self._running = False

    def stop(self) -> None:
        """Stop the HTTP server."""
        if not self._running:
            return

        self._running = False
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            logger.info("HTTP Modbus server stopped")

    def is_running(self) -> bool:
        """Check if server is running.

        Returns:
            True if running, False otherwise.
        """
        return self._running
