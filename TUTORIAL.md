# SunGather Charm Tutorial

This tutorial will guide you through deploying and configuring the SunGather charm to collect data from your Sungrow solar inverter.

## Prerequisites

- A Juju controller set up and configured
- A Kubernetes cluster (or access to a public cloud with Kubernetes support)
- A Sungrow solar inverter accessible over the network
- The inverter's IP address and port (typically 502 for ModBus TCP)

## Step 1: Deploy the charm

First, deploy the SunGather charm:

```bash
juju deploy sungather --resource sungather-image=bohdans/sungather:latest
```

Check the deployment status:

```bash
juju status sungather
```

You'll notice the charm is in a `blocked` state with the message "Config error: inverter-host is required". This is expected as we haven't configured the inverter connection yet.

## Step 2: Configure the inverter connection

Configure the charm with your inverter's details:

```bash
juju config sungather \
  inverter-host=192.168.1.100 \
  inverter-port=502 \
  connection-type=modbus
```

Replace `192.168.1.100` with your inverter's actual IP address.

Wait for the charm to settle:

```bash
juju status --watch 5s
```

Once the charm reaches `active` status, SunGather is collecting data from your inverter.

## Step 3: Test the connection

You can test the connection to your inverter using the `test-connection` action:

```bash
juju run sungather/0 test-connection
```

This will attempt to connect to the inverter and collect a single data point.

## Step 4: Access the web interface

By default, SunGather runs a web interface on port 8080. To access it externally, you'll need to integrate with Traefik.

Deploy Traefik if you haven't already:

```bash
juju deploy traefik-k8s --channel latest/stable --trust
```

Wait for Traefik to be active:

```bash
juju status --watch 5s
```

Then integrate the charm:

```bash
juju integrate sungather:ingress traefik:ingress
```

Traefik will automatically configure routing for the SunGather web interface. You can access it via the Traefik ingress URL.

## Step 5: Configure MQTT export (optional)

If you want to export data to MQTT (for example, for Home Assistant integration):

First, configure the MQTT settings:

```bash
juju config sungather \
  enable-mqtt=true \
  mqtt-host=mqtt.local \
  mqtt-port=1883 \
  mqtt-topic=solar/inverter \
  mqtt-homeassistant=true
```

If your MQTT broker requires authentication, add the credentials as secrets:

```bash
# Create secrets
juju add-secret mqtt-username value=myusername
juju add-secret mqtt-password value=mypassword

# Grant access to the charm
juju grant-secret mqtt-username sungather
juju grant-secret mqtt-password sungather
```

The charm will automatically pick up these secrets and use them for MQTT authentication.

## Step 6: Configure InfluxDB export (optional)

To export data to InfluxDB for time-series analysis:

```bash
juju config sungather \
  enable-influxdb=true \
  influxdb-host=influxdb.local \
  influxdb-port=8086 \
  influxdb-database=solar \
  influxdb-version=2
```

Add your InfluxDB authentication token as a secret:

```bash
juju add-secret influxdb-token value=your-token-here
juju grant-secret influxdb-token sungather
```

## Step 7: Configure PVOutput export (optional)

To upload data to [PVOutput.org](https://pvoutput.org):

First, enable PVOutput:

```bash
juju config sungather pvoutput-enabled=true
```

Then add your PVOutput credentials as secrets:

```bash
juju add-secret pvoutput-api-key value=your-api-key
juju add-secret pvoutput-system-id value=your-system-id
juju grant-secret pvoutput-api-key sungather
juju grant-secret pvoutput-system-id sungather
```

## Step 8: Adjust scan interval and data level

You can customise how frequently data is collected and how much data to collect:

```bash
# Collect data every 60 seconds instead of every 30
juju config sungather scan-interval=60

# Collect all available data (level 3)
juju config sungather level=3
```

Available levels:
- **Level 1** (default): Essential data only
- **Level 2**: Complete supported data
- **Level 3**: All registers including unsupported ones

## Step 9: Run an on-demand data collection

You can trigger a data collection cycle at any time using the `run-once` action:

```bash
juju run sungather/0 run-once
```

This is useful for testing or getting immediate data without waiting for the next scheduled scan.

## Step 10: Get inverter information

To retrieve information about your inverter:

```bash
juju run sungather/0 get-inverter-info
```

This will show the current configuration and connection status.

## Troubleshooting

### Charm is in blocked state

If the charm shows a blocked status:

```bash
juju status sungather
```

The status message will indicate what configuration is missing or invalid. Common issues:
- `inverter-host is required`: Set the inverter-host configuration
- `mqtt-host is required when enable-mqtt is true`: Either disable MQTT or configure mqtt-host
- `connection-type must be modbus, sungrow, or http`: Fix the connection-type value

### Cannot connect to inverter

If you're having connection issues:

1. Verify the inverter IP address is correct
2. Ensure the inverter is reachable from the Kubernetes cluster
3. Check the port number (502 for ModBus TCP, 8082 for HTTP)
4. Try the test-connection action: `juju run sungather/0 test-connection`

### View logs

To see what's happening inside the charm:

```bash
juju debug-log --replay --include=sungather
```

## Next steps

- Configure multiple export destinations simultaneously (MQTT + InfluxDB + PVOutput)
- Set up Grafana dashboards using the InfluxDB data
- Integrate with Home Assistant using MQTT discovery
- Monitor your solar production and household consumption patterns

## Further reading

- [SunGather documentation](https://sungather.net)
- [Juju documentation](https://juju.is/docs)
- [Home Assistant integration guide](https://www.home-assistant.io/integrations/mqtt/)
