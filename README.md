# SunGather Charm

A Juju charm for deploying and managing [SunGather](https://sungather.net), a data collection tool for Sungrow solar inverters.

## Overview

SunGather collects operational data from Sungrow inverters via ModBus connections and exports it to multiple platforms including MQTT, InfluxDB, PVOutput.org, and a built-in web interface.

### Features

- **Automatic inverter detection**: Automatically detects inverter model on first connection
- **Multiple export options**: MQTT, InfluxDB, PVOutput.org, and built-in webserver
- **Home Assistant integration**: Native MQTT discovery support
- **Flexible configuration**: Configurable scan intervals, data collection levels, and smart meter support
- **Secure credential management**: Uses Juju secrets for sensitive credentials
- **Actions**: Run data collection on-demand, test connections, and retrieve inverter information

## Important: OCI Image Issue

**The default OCI image (`bohdans/sungather:latest`) has missing Python dependencies and will not work.**

The charm will deploy successfully but the service will fail to start with:
```
ModuleNotFoundError: No module named 'SungrowClient'
```

The charm will show `blocked` status with the message:
```
service failed to start: check 'juju debug-log --include=sungather' for details, verify OCI image is correct
```

**Solution: Build the Working Rock Image**

This repository includes a working rock definition in the `rock/` directory. To build it:

```bash
cd rock
rockcraft pack
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  docker-daemon:sungather:0.3.8
```

See [rock/README.md](rock/README.md) for detailed instructions.

The integration tests verify that the charm handles broken workload images gracefully - this is working as designed. The rock provides a production-ready OCI image.

## Usage

### Basic deployment

```bash
# Deploy the charm
juju deploy sungather --resource sungather-image=bohdans/sungather:latest

# Configure the inverter connection
juju config sungather \
  inverter-host=192.168.1.100 \
  inverter-port=502 \
  connection-type=modbus \
  scan-interval=30

# Check the status
juju status sungather
```

### Enable MQTT export

```bash
# Configure MQTT settings
juju config sungather \
  enable-mqtt=true \
  mqtt-host=mqtt.local \
  mqtt-port=1883 \
  mqtt-topic=solar/inverter \
  mqtt-homeassistant=true

# Add MQTT credentials as secrets
juju add-secret mqtt-username value=myuser
juju add-secret mqtt-password value=mypassword
juju grant-secret mqtt-username sungather
juju grant-secret mqtt-password sungather
```

### Enable InfluxDB export

```bash
# Configure InfluxDB settings
juju config sungather \
  enable-influxdb=true \
  influxdb-host=influxdb.local \
  influxdb-port=8086 \
  influxdb-database=solar \
  influxdb-version=2

# Add InfluxDB token as secret
juju add-secret influxdb-token value=my-influxdb-token
juju grant-secret influxdb-token sungather
```

### Enable PVOutput export

```bash
# Enable PVOutput
juju config sungather pvoutput-enabled=true

# Add PVOutput credentials as secrets
juju add-secret pvoutput-api-key value=my-api-key
juju add-secret pvoutput-system-id value=my-system-id
juju grant-secret pvoutput-api-key sungather
juju grant-secret pvoutput-system-id sungather
```

### Access the web interface

```bash
# The webserver is enabled by default on port 8080
# To make it accessible externally, integrate with Traefik
juju deploy traefik-k8s --channel latest/stable --trust
juju integrate sungather:ingress traefik:ingress
```

### Actions

```bash
# Run a single data collection cycle
juju run sungather/0 run-once

# Get inverter information
juju run sungather/0 get-inverter-info

# Test connection to the inverter
juju run sungather/0 test-connection
```

## Configuration Options

### Inverter Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `inverter-host` | string | (required) | IP address or hostname of the inverter |
| `inverter-port` | int | 502 | Port for ModBus connection (502 for modbus, 8082 for HTTP) |
| `connection-type` | string | modbus | Connection type (modbus, sungrow, or http) |
| `inverter-model` | string | | Specific inverter model (auto-detected if not set) |
| `scan-interval` | int | 30 | Seconds between data collection cycles |
| `smart-meter` | boolean | false | Enable smart meter for consumption calculation |
| `level` | int | 1 | Register level (1=essential, 2=complete, 3=all) |

### Export Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable-webserver` | boolean | true | Enable built-in web interface |
| `webserver-port` | int | 8080 | Port for web interface |
| `enable-mqtt` | boolean | false | Enable MQTT export |
| `mqtt-host` | string | | MQTT broker hostname |
| `mqtt-port` | int | 1883 | MQTT broker port |
| `mqtt-topic` | string | sungather | MQTT topic prefix |
| `mqtt-homeassistant` | boolean | false | Enable Home Assistant MQTT discovery |
| `enable-influxdb` | boolean | false | Enable InfluxDB export |
| `influxdb-host` | string | | InfluxDB hostname |
| `influxdb-port` | int | 8086 | InfluxDB port |
| `influxdb-database` | string | sungather | InfluxDB database name |
| `influxdb-version` | int | 2 | InfluxDB version (1 or 2) |
| `pvoutput-enabled` | boolean | false | Enable PVOutput.org export |
| `log-level` | string | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Integrations

### Ingress

The charm integrates with Traefik to expose the web interface externally:

```bash
# Deploy Traefik if not already deployed
juju deploy traefik-k8s --channel latest/stable --trust

# Integrate with SunGather
juju integrate sungather:ingress traefik:ingress
```

Once integrated, Traefik will automatically configure routing to the SunGather web interface.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for information on how to develop and test this charm.

## Tutorial

For a step-by-step guide to deploying and using this charm, see [TUTORIAL.md](TUTORIAL.md).

## Security

To report security vulnerabilities, please see [SECURITY.md](SECURITY.md).

## Licence

This charm is distributed under the Apache Software Licence, version 2.0. See [LICENSE](LICENSE) for details.

## Project and community

- [SunGather upstream project](https://github.com/bohdan-s/SunGather)
- [Juju documentation](https://juju.is/docs)
