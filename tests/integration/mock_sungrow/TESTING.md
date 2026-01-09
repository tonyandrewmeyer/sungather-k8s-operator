# Running Integration Tests with Mock Server

The mock Sungrow server enables comprehensive integration testing of the charm with a working workload. However, these tests have specific requirements that must be met.

## Current Status

⚠️ **The tests in `test_charm_with_mock.py` are currently skipped** because they require a working OCI image.

The default OCI image (`bohdans/sungather:latest`) is broken and missing Python dependencies, so it cannot connect to the mock server (the workload container fails to start).

## Requirements for Running These Tests

### 1. Build the Working Rock

The `rock/` directory contains a working rock definition with all dependencies:

```bash
cd rock/
rockcraft pack
```

This creates `sungather_0.3.8_amd64.rock`.

### 2. Make the Image Available to Kubernetes

You have several options:

#### Option A: Local Registry (MicroK8s)

```bash
# Enable MicroK8s registry
microk8s enable registry

# Load the rock into local Docker
sudo rockcraft.skopeo --insecure-policy copy \
  oci-archive:sungather_0.3.8_amd64.rock \
  docker-daemon:sungather:0.3.8

# Push to MicroK8s registry
docker tag sungather:0.3.8 localhost:32000/sungather:0.3.8
docker push localhost:32000/sungather:0.3.8
```

#### Option B: External Registry

```bash
# Push to Docker Hub (or other registry)
docker tag sungather:0.3.8 yourusername/sungather:0.3.8
docker push yourusername/sungather:0.3.8
```

### 3. Update the Test Configuration

Edit `tests/integration/test_charm_with_mock.py` and:

1. Remove or comment out the `pytestmark = pytest.mark.skip(...)` line
2. Update the resource configuration to use your image:

```python
resources = {
    "sungather-image": "localhost:32000/sungather:0.3.8"  # Or your registry URL
}
```

### 4. Get Host IP Address

The mock server needs to be accessible from inside the Kubernetes pod. Get your host IP:

```bash
hostname -I | awk '{print $1}'
```

Update the test configuration to use this IP instead of `127.0.0.1`:

```python
conn_info = mock_sungrow.get_connection_info("modbus")
config = {
    "inverter-host": "10.21.40.247",  # Use your actual host IP
    "inverter-port": conn_info["port"],
    "connection-type": "modbus",
}
```

### 5. Run the Tests

```bash
pytest tests/integration/test_charm_with_mock.py -v
```

## Expected Results

When properly configured, these tests should:

- ✅ Deploy the charm with a working workload
- ✅ Verify charm reaches **active** status (not blocked)
- ✅ Test that actions (`run-once`, `test-connection`) succeed
- ✅ Verify MQTT and webserver configurations work
- ✅ Test configuration changes maintain active status

## Troubleshooting

### Test fails with "service failed to start"

The OCI image is broken or missing dependencies. Verify you're using the rock you built, not the default image.

### Test fails with "connection refused"

The mock server isn't accessible from the pod. Check:
- Mock server is bound to `0.0.0.0` (not `127.0.0.1`)
- You're using the host IP address in the configuration
- Firewall rules allow access to ports 5020 and 8082

### Test times out waiting for active status

Check the Juju logs:
```bash
juju debug-log --include=sungather
```

Look for errors about connecting to the inverter host.

## Alternative: Skip Network Issues

If you can't get the networking to work, you can still verify the mock server works standalone:

```python
from mock_sungrow import MockSungrowServer

server = MockSungrowServer(host="0.0.0.0", modbus_port=5020)
server.start()

# Test register access
values = server.registers.read_input_registers(5000, 5)
print(f"Registers: {values}")

server.stop()
```

## Future Improvements

Potential enhancements to make these tests easier to run:

1. **In-cluster mock server**: Deploy the mock server as a Kubernetes service
2. **Automatic rock building**: Add CI step to build and push the rock
3. **Test fixtures for image selection**: Auto-detect if working image is available
4. **Host network mode**: Run tests in a way that makes localhost accessible

## See Also

- [Mock Server README](README.md) - Architecture and API documentation
- [Rock README](../../../rock/README.md) - Building the working OCI image
- [CONTRIBUTING.md](../../../CONTRIBUTING.md) - Development setup
