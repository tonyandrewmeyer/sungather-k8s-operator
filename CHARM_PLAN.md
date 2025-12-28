# SunGather Charm Plan

## Overview

SunGather is a Python application that collects operational data from Sungrow solar inverters via ModBus connections and exports the data to multiple platforms (MQTT, InfluxDB, PVOutput, web interface).

## Charm Type: Kubernetes

**Rationale:**
- The application has native Docker support
- Lightweight Python service suitable for containerisation
- No special hardware requirements (network-based ModBus connection)
- Enables deployment in modern cloud and on-premises Kubernetes environments
- Better resource isolation and management

## OCI Image

The charm will use the official Docker image: `bohdans/sungather:latest`

We may need to consider creating a Rock (Ubuntu-based OCI image) in the future for better integration, but starting with the existing Docker image is appropriate.

## Configuration

The charm will expose the following configuration options in `config.yaml` of the charm:

### Inverter Settings
- `inverter-host` (string, required): IP address or hostname of the Sungrow inverter
- `inverter-port` (int, default: 502): Port for ModBus connection (502 for modbus, 8082 for HTTP)
- `connection-type` (string, default: "modbus"): Connection type - "modbus", "sungrow", or "http"
- `inverter-model` (string, optional): Specific inverter model (auto-detected if not provided)
- `scan-interval` (int, default: 30): Seconds between data collection cycles
- `smart-meter` (boolean, default: false): Enable smart meter for household consumption calculation
- `level` (int, default: 1): Register level (1=essential, 2=complete, 3=all including unsupported)

### Export Settings
- `enable-webserver` (boolean, default: true): Enable built-in web interface
- `webserver-port` (int, default: 8080): Port for web interface
- `enable-mqtt` (boolean, default: false): Enable MQTT export
- `mqtt-host` (string, optional): MQTT broker hostname
- `mqtt-port` (int, default: 1883): MQTT broker port
- `mqtt-topic` (string, default: "sungather"): MQTT topic prefix
- `mqtt-homeassistant` (boolean, default: false): Enable Home Assistant MQTT discovery
- `enable-influxdb` (boolean, default: false): Enable InfluxDB export
- `pvoutput-enabled` (boolean, default: false): Enable PVOutput.org export

### Logging
- `log-level` (string, default: "INFO"): Logging verbosity (DEBUG, INFO, WARNING, ERROR)

## Secrets

For sensitive configuration:
- `mqtt-username` (secret): MQTT broker username
- `mqtt-password` (secret): MQTT broker password
- `influxdb-token` (secret): InfluxDB authentication token
- `pvoutput-api-key` (secret): PVOutput.org API key
- `pvoutput-system-id` (secret): PVOutput.org system ID

## Integrations (Relations)

### Provides
- `grafana-dashboard` (optional): Provide dashboards for Grafana
- `metrics-endpoint` (optional): Prometheus metrics endpoint if we add prometheus export

### Requires
- `ingress` (optional): Integration with ingress controller for web UI access
- `mqtt` (optional): Integration with MQTT broker charm (if available)

## Actions

### `run-once`
Execute a single data collection cycle without waiting for the scheduled interval.

**Parameters:** None

**Returns:** Success/failure status and collected data summary

### `get-inverter-info`
Retrieve detected inverter model and connection status.

**Parameters:** None

**Returns:** Inverter model, firmware version, connection status

### `test-connection`
Test the connection to the inverter without starting data collection.

**Parameters:** None

**Returns:** Connection test result (success/failure, latency, errors)

## Storage

No persistent storage is required as SunGather operates as a data pipeline. Logs can be ephemeral or handled via Kubernetes logging infrastructure.

## Scaling

- **Single unit**: SunGather typically monitors one inverter per instance
- **Multiple units**: Each unit would need to be configured for a different inverter
- This is a single-unit charm (doesn't make sense to scale horizontally for the same inverter)

## Pebble Layer

The Pebble service definition will:
- Run the sungather Python application with configuration from charm config
- Mount a generated `config.yaml` based on Juju configuration
- Expose port 8080 for web interface
- Handle restart on failure
- Pass appropriate environment variables (TZ, log level)

## Implementation Phases

### Phase 1: Basic Functionality
1. Initialise Kubernetes charm
2. Configure Pebble layer to run sungather
3. Implement configuration handling (config.yaml generation)
4. Implement basic inverter connection configuration
5. Enable webserver export
6. Test with a basic deployment

### Phase 2: Exports
1. Implement MQTT configuration and secrets
2. Implement InfluxDB configuration and secrets
3. Implement PVOutput configuration and secrets
4. Add validation for export settings

### Phase 3: Integrations
1. Add ingress integration for web UI
2. Add MQTT integration (if charm exists)
3. Add Prometheus metrics export (enhancement)

### Phase 4: Actions
1. Implement `run-once` action
2. Implement `get-inverter-info` action
3. Implement `test-connection` action

### Phase 5: Testing & Documentation
1. Comprehensive integration tests
2. Unit tests for configuration handling
3. Update README with deployment instructions
4. Create TUTORIAL.md
5. Create CONTRIBUTING.md
6. Add security and conduct files

## Edge Cases & Considerations

1. **Configuration validation**: Ensure required fields are present when exports are enabled
2. **Network connectivity**: Handle scenarios where inverter is unreachable
3. **Secrets management**: Proper handling of sensitive credentials via Juju secrets
4. **Port conflicts**: Validate webserver port is available
5. **Container health**: Monitor sungather process and restart on failure
6. **Config changes**: Properly handle configuration updates and restart service

## Testing Strategy

### Integration Tests
- Deploy charm and verify Pebble service starts
- Configure inverter settings and verify config.yaml generation
- Enable webserver and verify port accessibility
- Test configuration updates trigger service restart
- Test secret management for MQTT/InfluxDB credentials
- Test actions execute correctly

### Unit Tests
- Config.yaml generation from charm config
- Pebble layer construction
- Configuration validation
- Event handlers (config-changed, start, update-status)

## Documentation

- **README.md**: Overview, quick start, features
- **CONTRIBUTING.md**: Development setup, testing, contribution guidelines
- **TUTORIAL.md**: Step-by-step deployment guide with example configurations
- **SECURITY.md**: Security reporting process
- **CODE_OF_CONDUCT.md**: Community guidelines
- **CHANGELOG.md**: Version history and notable changes
