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

### Option 1: Push to a Container Registry (Recommended)

Push the rock directly to a container registry:

```bash
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  docker://your-registry/sungather:0.3.8
```

### Option 2: Load into Local Container Runtime

For MicroK8s:
```bash
# Convert to OCI tar format
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  oci-archive:/tmp/sungather.tar

# Import into MicroK8s
sudo microk8s ctr image import /tmp/sungather.tar
```

For Docker:
```bash
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  docker-daemon:sungather:0.3.8
```

For Canonical K8s (k8s snap):
```bash
# Convert to OCI tar format first
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  oci-archive:/tmp/sungather.tar

# Then use your container runtime to import
# Note: May require additional setup or a local registry
```

## Using with the Charm

### Deploy with Registry Image (Recommended)

```bash
juju deploy sungather --resource sungather-image=your-registry/sungather:0.3.8
```

### Deploy with Local Image

If you've loaded the image into your local container runtime:

```bash
juju deploy sungather --resource sungather-image=localhost/sungather:0.3.8
```

## What's Included

The rock includes:
- Python 3.10 runtime
- Python virtual environment created with `uv` (fast Python package manager)
- SunGather application from the official GitHub repository
- All required Python dependencies (20 packages):
  - certifi, charset-normalizer, idna, urllib3, requests
  - paho-mqtt (MQTT client)
  - pymodbus, pyserial (ModBus communication)
  - sungrowclient, sungrowmodbustcpclient, sungrowmodbuswebclient (Sungrow-specific clients)
  - influxdb-client (InfluxDB export)
  - pyyaml (YAML configuration)
  - pycryptodomex (encryption)
  - reactivex, python-dateutil, typing-extensions, websocket-client
  - setuptools, six

## Build Process

This rock uses `uv` (from the `astral-uv` snap) for fast dependency management:
1. Clones the official SunGather repository from GitHub
2. Creates a Python 3.10 virtual environment using `uv venv`
3. Installs all dependencies from `requirements.txt` using `uv pip install`
4. Copies application files to `/opt/sungather/`
5. Configures Pebble service to run the application

**Build time**: Dependencies install in ~23ms thanks to uv's speed!

## Directory Structure

Inside the rock:
- `/opt/sungather/SunGather/` - SunGather application files
- `/opt/sungather/SunGather/sungather.py` - Main application script
- `/opt/venv/` - Python virtual environment with all dependencies
- `/config/` - Expected location for config.yaml (mounted by charm)

## Testing Locally

You can test the rock locally before deploying:

```bash
docker run -it -v $(pwd)/config.yaml:/config/config.yaml sungather:0.3.8
```

Make sure you have a valid `config.yaml` file with your inverter settings.

## Troubleshooting

### ModuleNotFoundError: No module named 'SungrowClient'

This error occurs with the default `bohdans/sungather:latest` image because it's missing Python dependencies. This rock solves that problem by including all required dependencies in the virtual environment.

### Rock Build Fails

If the rock build fails:
1. Ensure `rockcraft` is installed: `sudo snap install rockcraft --classic`
2. Check that you have internet connectivity (required to clone repository and download dependencies)
3. Clean previous build artifacts: `rockcraft clean`
4. Try building again: `rockcraft pack`
