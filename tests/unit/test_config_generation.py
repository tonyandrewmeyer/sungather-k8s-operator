# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# State-transition tests for the SunGather configuration file the charm renders
# and the Pebble layer it applies. These run the real charm via ops.testing and
# inspect the resulting container, rather than calling private methods directly.

import yaml
from ops import pebble, testing

from charm import CONTAINER_NAME, SERVICE_NAME, SungatherCharm

# The reconcile flow reads the workload version with `python3 -c ...`; register an
# exec so the simulated container can answer without a real workload.
VERSION_EXEC = testing.Exec(["/usr/bin/python3.10", "-c"], stdout="0.3.8\n")


def _container(**kwargs):
    """Build a ready container with the version exec registered."""
    return testing.Container(
        CONTAINER_NAME,
        can_connect=True,
        execs={VERSION_EXEC},
        service_statuses={SERVICE_NAME: pebble.ServiceStatus.INACTIVE},
        **kwargs,
    )


def _rendered_config(config, secrets=()):
    """Run config-changed and return the parsed config.yaml pushed to the container."""
    ctx = testing.Context(SungatherCharm)
    state_in = testing.State(containers={_container()}, secrets=set(secrets), config=config)
    state_out = ctx.run(ctx.on.config_changed(), state_in)
    root = state_out.get_container(CONTAINER_NAME).get_filesystem(ctx)
    return yaml.safe_load((root / "config" / "config.yaml").read_text())


def _export(config_dict, name):
    for export in config_dict["exports"]:
        if export["name"] == name:
            return export
    raise AssertionError(f"no {name!r} export found in {config_dict['exports']}")


def test_basic_inverter_and_webserver():
    """A minimal valid config renders the inverter section and webserver export."""
    rendered = _rendered_config({"inverter-host": "192.168.1.100"})

    assert rendered["inverter"]["host"] == "192.168.1.100"
    assert rendered["inverter"]["port"] == 502
    assert rendered["inverter"]["connection"] == "modbus"
    assert rendered["inverter"]["scan_interval"] == 30
    assert rendered["inverter"]["level"] == 1
    assert rendered["inverter"]["smart_meter"] is False

    webserver = _export(rendered, "webserver")
    assert webserver is not None
    assert webserver["enabled"] is True
    assert webserver["port"] == 8080


def test_mqtt_export():
    """Enabling MQTT renders an MQTT export with the configured broker."""
    rendered = _rendered_config(
        {
            "inverter-host": "192.168.1.100",
            "enable-webserver": False,
            "enable-mqtt": True,
            "mqtt-host": "mqtt.example.com",
            "mqtt-topic": "solar/inverter",
            "mqtt-homeassistant": True,
        }
    )

    mqtt = _export(rendered, "mqtt")
    assert mqtt is not None
    assert mqtt["host"] == "mqtt.example.com"
    assert mqtt["port"] == 1883
    assert mqtt["topic"] == "solar/inverter"
    assert mqtt["homeassistant"] is True


def test_mqtt_credentials_injected_from_secrets():
    """MQTT credentials stored as Juju secrets are written into the config file."""
    secrets = [
        testing.Secret(
            tracked_content={"value": "broker-user"}, label="mqtt-username", owner="app"
        ),
        testing.Secret(
            tracked_content={"value": "broker-pass"}, label="mqtt-password", owner="app"
        ),
    ]
    rendered = _rendered_config(
        {
            "inverter-host": "192.168.1.100",
            "enable-webserver": False,
            "enable-mqtt": True,
            "mqtt-host": "mqtt.example.com",
        },
        secrets=secrets,
    )

    mqtt = _export(rendered, "mqtt")
    assert mqtt["username"] == "broker-user"
    assert mqtt["password"] == "broker-pass"


def test_influxdb_export():
    """Enabling InfluxDB renders an InfluxDB export with the configured database."""
    rendered = _rendered_config(
        {
            "inverter-host": "192.168.1.100",
            "enable-webserver": False,
            "enable-influxdb": True,
            "influxdb-host": "influxdb.example.com",
            "influxdb-database": "solar",
        }
    )

    influxdb = _export(rendered, "influxdb")
    assert influxdb is not None
    assert influxdb["host"] == "influxdb.example.com"
    assert influxdb["port"] == 8086
    assert influxdb["database"] == "solar"
    assert influxdb["version"] == 2


def test_influxdb_token_injected_from_secret():
    """An InfluxDB token stored as a Juju secret is written into the config file."""
    secrets = [
        testing.Secret(
            tracked_content={"value": "influx-token"}, label="influxdb-token", owner="app"
        ),
    ]
    rendered = _rendered_config(
        {
            "inverter-host": "192.168.1.100",
            "enable-webserver": False,
            "enable-influxdb": True,
            "influxdb-host": "influxdb.example.com",
        },
        secrets=secrets,
    )

    assert _export(rendered, "influxdb")["token"] == "influx-token"


def test_pvoutput_export_with_secrets():
    """Enabling PVOutput renders an export with credentials from Juju secrets."""
    secrets = [
        testing.Secret(
            tracked_content={"value": "api-key"}, label="pvoutput-api-key", owner="app"
        ),
        testing.Secret(
            tracked_content={"value": "sys-id"}, label="pvoutput-system-id", owner="app"
        ),
    ]
    rendered = _rendered_config(
        {
            "inverter-host": "192.168.1.100",
            "enable-webserver": False,
            "pvoutput-enabled": True,
        },
        secrets=secrets,
    )

    pvoutput = _export(rendered, "pvoutput")
    assert pvoutput is not None
    assert pvoutput["api_key"] == "api-key"
    assert pvoutput["system_id"] == "sys-id"


def test_pebble_layer_and_environment():
    """The applied Pebble plan runs SunGather with the expected command and env."""
    ctx = testing.Context(SungatherCharm)
    state_in = testing.State(
        containers={_container()},
        config={"inverter-host": "192.168.1.100", "log-level": "DEBUG"},
    )

    state_out = ctx.run(ctx.on.config_changed(), state_in)

    service = state_out.get_container(CONTAINER_NAME).plan.services[SERVICE_NAME]
    assert service.command == "/usr/bin/python3.10 sungather.py -c /config/config.yaml"
    assert service.working_dir == "/opt/sungather/SunGather"
    assert service.environment["TZ"] == "UTC"
    assert service.environment["LOG_LEVEL"] == "10"  # DEBUG maps to 10.
    assert service.environment["PYTHONPATH"] == "/opt/sungather-lib"
    assert state_out.workload_version == "0.3.8"
