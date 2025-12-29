# SunGather Rock

This directory contains the rockcraft definition for building a working SunGather OCI image.

## Building the Rock

Install rockcraft if you haven't already:

```bash
sudo snap install rockcraft --classic
```

Build the rock:

```bash
cd rock
rockcraft pack
```

This will create a rock file like `sungather_0.3.8_amd64.rock`.

## Converting to OCI Image

Convert the rock to an OCI image:

```bash
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  docker-daemon:sungather:0.3.8
```

Or push directly to a registry:

```bash
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  docker://your-registry/sungather:0.3.8
```

## Using with the Charm

Deploy the charm with your custom rock:

```bash
# If using local Docker image
docker save sungather:0.3.8 | microk8s ctr image import -

# Deploy the charm
juju deploy sungather --resource sungather-image=sungather:0.3.8
```

Or if you pushed to a registry:

```bash
juju deploy sungather --resource sungather-image=your-registry/sungather:0.3.8
```

## What's Included

The rock includes:
- Python 3 with a virtual environment
- SunGather application from the official GitHub repository
- All required Python dependencies:
  - paho-mqtt
  - pymodbus
  - SungrowModbusTcpClient
  - SungrowModbusWebClient
  - PyYAML
  - requests
  - influxdb-client

## Directory Structure

Inside the rock:
- `/opt/sungather/` - SunGather application files
- `/opt/sungather/sungather.py` - Main application script
- `/opt/venv/` - Python virtual environment with dependencies
- `/config/` - Expected location for config.yaml (mounted by charm)

## Testing Locally

You can test the rock locally before deploying:

```bash
docker run -it -v $(pwd)/config.yaml:/config/config.yaml sungather:0.3.8
```

Make sure you have a valid `config.yaml` file with your inverter settings.
