# Mock Sungrow Inverter Server

This directory contains a mock Sungrow inverter server for integration testing. The mock server simulates both Modbus TCP and HTTP/WebSocket protocols used by real Sungrow inverters, allowing comprehensive testing without requiring actual hardware.

## Overview

The mock server implements:

- **Modbus TCP** (port 5020): Standard Modbus TCP protocol with Sungrow register map
- **HTTP/WebSocket** (port 8082): WiNet-S protocol that wraps Modbus RTU packets in HTTP

## Architecture

```
mock_sungrow/
├── __init__.py          # Public API
├── server.py            # Main orchestrator (MockSungrowServer)
├── modbus_server.py     # Modbus TCP implementation
├── http_server.py       # HTTP/WebSocket implementation
├── registers.py         # Sungrow register map with dummy data
└── README.md            # This file
```

## Usage

### In Integration Tests

The mock server is available as a pytest fixture in `conftest.py`:

```python
def test_deploy_with_mock(charm, juju, mock_sungrow):
    """Test deployment with mock Sungrow server."""
    # Get connection info
    conn_info = mock_sungrow.get_connection_info("modbus")

    config = {
        "inverter-host": conn_info["host"],
        "inverter-port": conn_info["port"],
        "connection-type": "modbus",
    }

    juju.deploy(charm, config=config, ...)
    juju.wait(jubilant.all_active, timeout=180)
```

### Standalone Usage

You can also run the mock server standalone for manual testing:

```python
from tests.integration.mock_sungrow import MockSungrowServer

# Start both Modbus and HTTP servers
server = MockSungrowServer(
    host="127.0.0.1",
    modbus_port=5020,
    http_port=8082,
    model="SG5K-D",
    server_type="both"
)
server.start()

# Use the server...

server.stop()
```

### Connection Types

The mock server supports all three connection types that the charm supports:

1. **Modbus TCP** (`connection-type: modbus`)
   ```yaml
   inverter-host: 127.0.0.1
   inverter-port: 5020
   connection-type: modbus
   ```

2. **HTTP** (`connection-type: http`)
   ```yaml
   inverter-host: 127.0.0.1
   inverter-port: 8082
   connection-type: http
   ```

3. **Sungrow** (`connection-type: sungrow`)
   Currently implemented as standard Modbus TCP (encryption not yet supported)

## Register Map

The mock server implements a subset of the Sungrow register map with realistic dummy data:

- **Device information** (registers 4999-5022): Model, firmware version
- **Real-time data** (registers 5000-5200): Voltages, currents, power, energy
- **Status** (registers 5007-5009): Temperature, running status, fault codes

Registers are updated dynamically to simulate changing power output and energy accumulation.

## Features

### Realistic Simulation

- Returns valid Modbus responses
- Simulates power output variations
- Increments daily energy counters
- Supports both holding and input registers

### Multiple Server Types

Start only the servers you need:

```python
# Modbus only
server = MockSungrowServer(server_type="modbus")

# HTTP only
server = MockSungrowServer(server_type="http")

# Both (default)
server = MockSungrowServer(server_type="both")
```

### Configurable Models

Simulate different inverter models:

```python
server = MockSungrowServer(model="SG5K-D")   # 5kW inverter
server = MockSungrowServer(model="SG10RT")   # 10kW inverter
```

## Testing Benefits

The mock server enables:

1. **Positive Path Testing**: Verify charm works with functioning workload
2. **Action Testing**: Test run-once, test-connection, get-inverter-info actions
3. **Configuration Testing**: Verify different connection types work correctly
4. **CI/CD Integration**: No hardware required for automated testing
5. **Fast Iteration**: Instant feedback without physical inverter
6. **Error Simulation**: Can be extended to simulate various error conditions

## Limitations

Current limitations (potential future improvements):

- Does not implement Sungrow's encrypted Modbus protocol
- WebSocket implementation is simplified (not full WiNet-S protocol)
- Register map is not exhaustive (subset of common registers)
- Does not simulate all inverter models
- Does not simulate network errors or timeouts

## Extending the Mock Server

### Adding Registers

Edit `registers.py` to add more registers:

```python
def _initialise_registers(self) -> None:
    # Add your registers here
    self._registers[5100] = 1234  # New register
```

### Simulating Errors

You can extend the servers to simulate error conditions:

```python
class FaultyModbusDataBlock(SungrowModbusDataBlock):
    def getValues(self, address: int, count: int = 1) -> list[int]:
        if address == 5009:  # Fault code register
            return [42]  # Simulate fault
        return super().getValues(address, count)
```

## Dependencies

- `pymodbus>=3.0` - Modbus TCP server implementation
- Standard library: `http.server`, `json`, `threading`

## See Also

- [SunGather documentation](https://sungather.net/)
- [Sungrow register map discussions](https://forums.whirlpool.net.au/archive/2560277)
- [pymodbus documentation](https://pymodbus.readthedocs.io/)
