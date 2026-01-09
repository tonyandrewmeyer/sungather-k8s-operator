# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial charm implementation for SunGather
- Traefik ingress integration for external access to web interface
- Configuration options for inverter connection (host, port, connection type, scan interval)
- Support for multiple export destinations:
  - Built-in webserver (enabled by default on port 8080)
  - MQTT with Home Assistant discovery support
  - InfluxDB (versions 1.8 and 2.x)
  - PVOutput.org
- Juju secrets integration for secure credential management
- Three charm actions:
  - `run-once`: Execute a single data collection cycle
  - `get-inverter-info`: Retrieve inverter model and connection status
  - `test-connection`: Test connection to the inverter
- Ingress integration for external access to the web interface
- Smart meter support for household consumption calculation
- Configurable data collection levels (1=essential, 2=complete, 3=all registers)
- Configurable logging levels (DEBUG, INFO, WARNING, ERROR)
- Comprehensive integration tests using Jubilant
- Comprehensive unit tests using ops.testing
- Mock Sungrow inverter server for integration testing
  - Implements Modbus TCP protocol with realistic register data using pymodbus 3.x
  - Implements HTTP/WebSocket protocol (WiNet-S simulation)
  - Supports both `modbus` and `http` connection types
  - Enables testing charm with working workload without hardware
  - Tests currently skipped (require working OCI image from rock/ directory)
  - See `tests/integration/mock_sungrow/README.md` and `TESTING.md` for details
- Working rock definition in `rock/` directory for building production-ready OCI images
  - Uses `uv` for fast dependency management (dependencies install in ~23ms)
  - Includes all 20 required Python packages (paho-mqtt, pymodbus, sungrowclient, influxdb-client, etc.)
  - Resolves ModuleNotFoundError present in default `bohdans/sungather:latest` image
  - Comprehensive build and deployment documentation in `rock/README.md`
- Documentation:
  - README with usage examples
  - TUTORIAL for step-by-step deployment guide
  - CONTRIBUTING for development guidelines
  - SECURITY for vulnerability reporting
  - Rock build instructions and troubleshooting guide

### Changed
- CI workflow now uses `uv` for faster test execution
- CI workflow uses Concierge for simplified Juju/K8s environment setup
- Integration tests clarified to verify charm robustness with broken workload images
- Error messages now include specific `juju config` commands for resolution

### Fixed
- Charm filename reference in CI workflow (corrected to `sungather_amd64.charm`)
- Concierge installation in CI now uses `--classic` flag

[Unreleased]: https://github.com/canonical/sungather-operator/compare/HEAD...HEAD
