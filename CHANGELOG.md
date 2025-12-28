# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial charm implementation for SunGather
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
- Documentation:
  - README with usage examples
  - TUTORIAL for step-by-step deployment guide
  - CONTRIBUTING for development guidelines
  - SECURITY for vulnerability reporting

[Unreleased]: https://github.com/canonical/sungather-operator/compare/HEAD...HEAD
