#!/usr/bin/env python3
# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.

"""Charm for SunGather - Solar inverter data collection."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import ops
import yaml
from charms.traefik_k8s.v2.ingress import (
    IngressPerAppReadyEvent,
    IngressPerAppRequirer,
    IngressPerAppRevokedEvent,
)

import sungather

logger = logging.getLogger(__name__)

CONTAINER_NAME = "sungather"
SERVICE_NAME = "sungather"
CONFIG_PATH = "/config/config.yaml"


@dataclass
class CharmConfig:
    """Configuration for the SunGather charm."""

    # Inverter settings
    inverter_host: str | None
    inverter_port: int
    connection_type: str
    inverter_model: str | None
    scan_interval: int
    smart_meter: bool
    level: int

    # Export settings
    enable_webserver: bool
    webserver_port: int
    enable_mqtt: bool
    mqtt_host: str | None
    mqtt_port: int
    mqtt_topic: str
    mqtt_homeassistant: bool
    enable_influxdb: bool
    influxdb_host: str | None
    influxdb_port: int
    influxdb_database: str
    influxdb_version: int
    pvoutput_enabled: bool

    # Logging
    log_level: str

    @classmethod
    def from_charm(cls, charm: SungatherCharm) -> CharmConfig:
        """Create a CharmConfig from charm configuration."""
        config = charm.config
        return cls(
            # Inverter settings
            inverter_host=config.get("inverter-host"),  # type: ignore[arg-type]
            inverter_port=config["inverter-port"],  # type: ignore[arg-type]
            connection_type=config["connection-type"],  # type: ignore[arg-type]
            inverter_model=config.get("inverter-model"),  # type: ignore[arg-type]
            scan_interval=config["scan-interval"],  # type: ignore[arg-type]
            smart_meter=config["smart-meter"],  # type: ignore[arg-type]
            level=config["level"],  # type: ignore[arg-type]
            # Export settings
            enable_webserver=config["enable-webserver"],  # type: ignore[arg-type]
            webserver_port=config["webserver-port"],  # type: ignore[arg-type]
            enable_mqtt=config["enable-mqtt"],  # type: ignore[arg-type]
            mqtt_host=config.get("mqtt-host"),  # type: ignore[arg-type]
            mqtt_port=config["mqtt-port"],  # type: ignore[arg-type]
            mqtt_topic=config["mqtt-topic"],  # type: ignore[arg-type]
            mqtt_homeassistant=config["mqtt-homeassistant"],  # type: ignore[arg-type]
            enable_influxdb=config["enable-influxdb"],  # type: ignore[arg-type]
            influxdb_host=config.get("influxdb-host"),  # type: ignore[arg-type]
            influxdb_port=config["influxdb-port"],  # type: ignore[arg-type]
            influxdb_database=config["influxdb-database"],  # type: ignore[arg-type]
            influxdb_version=config["influxdb-version"],  # type: ignore[arg-type]
            pvoutput_enabled=config["pvoutput-enabled"],  # type: ignore[arg-type]
            # Logging
            log_level=config["log-level"],  # type: ignore[arg-type]
        )

    def validate(self) -> list[str]:
        """Validate the configuration and return a list of errors."""
        errors = []

        # Inverter host is required
        if not self.inverter_host:
            errors.append(
                "missing inverter-host: set with "
                "'juju config sungather inverter-host=<ip-address>'"
            )

        # Connection type validation
        if self.connection_type not in ["modbus", "sungrow", "http"]:
            errors.append(
                f"invalid connection-type '{self.connection_type}': use "
                "'juju config sungather connection-type=modbus' (or sungrow/http)"
            )

        # Level validation
        if self.level not in [1, 2, 3]:
            errors.append(
                f"invalid level {self.level}: use 'juju config sungather level=1' "
                "(1=essential, 2=complete, 3=all)"
            )

        # MQTT validation
        if self.enable_mqtt and not self.mqtt_host:
            errors.append(
                "mqtt-host required when MQTT enabled: set with "
                "'juju config sungather mqtt-host=<hostname>' or disable with "
                "'juju config sungather enable-mqtt=false'"
            )

        # InfluxDB validation
        if self.enable_influxdb and not self.influxdb_host:
            errors.append(
                "influxdb-host required when InfluxDB enabled: set with "
                "'juju config sungather influxdb-host=<hostname>' or disable with "
                "'juju config sungather enable-influxdb=false'"
            )

        # Log level validation
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            errors.append(
                f"invalid log-level '{self.log_level}': use "
                "'juju config sungather log-level=INFO' (DEBUG/INFO/WARNING/ERROR)"
            )

        return errors


class SungatherCharm(ops.CharmBase):
    """Charm for SunGather application."""

    def __init__(self, framework: ops.Framework):
        super().__init__(framework)
        self.container = self.unit.get_container(CONTAINER_NAME)

        # Set up ingress integration
        self.ingress = IngressPerAppRequirer(
            self,
            port=self.config.get("webserver-port", 8080),  # type: ignore[arg-type]
            strip_prefix=True,
        )

        # Observe events
        framework.observe(self.on[CONTAINER_NAME].pebble_ready, self._on_pebble_ready)
        framework.observe(self.on.config_changed, self._on_config_changed)
        framework.observe(self.on.update_status, self._on_update_status)

        # Observe ingress events
        framework.observe(self.ingress.on.ready, self._on_ingress_ready)
        framework.observe(self.ingress.on.revoked, self._on_ingress_revoked)

        # Observe action events
        framework.observe(self.on.run_once_action, self._on_run_once_action)
        framework.observe(self.on.get_inverter_info_action, self._on_get_inverter_info_action)
        framework.observe(self.on.test_connection_action, self._on_test_connection_action)

    def _on_pebble_ready(self, event: ops.PebbleReadyEvent) -> None:
        """Handle pebble-ready event."""
        self._reconcile(event)

    def _on_config_changed(self, event: ops.ConfigChangedEvent) -> None:
        """Handle config-changed event."""
        self._reconcile(event)

    def _on_update_status(self, event: ops.UpdateStatusEvent) -> None:
        """Handle update-status event."""
        # Check if the service is running
        if not self.container.can_connect():
            return

        if self._is_service_running():
            self.unit.status = ops.ActiveStatus()
        else:
            self.unit.status = ops.BlockedStatus(
                "service not running: check 'juju debug-log' for errors, "
                "verify inverter is reachable"
            )

    def _on_ingress_ready(self, event: IngressPerAppReadyEvent) -> None:
        """Handle ingress-ready event."""
        logger.info("Ingress URL is ready: %s", event.url)

    def _on_ingress_revoked(self, event: IngressPerAppRevokedEvent) -> None:
        """Handle ingress-revoked event."""
        logger.info("Ingress has been revoked")

    def _reconcile(self, event: ops.EventBase) -> None:
        """Reconcile the charm state."""
        # Wait for container to be ready
        if not self.container.can_connect():
            event.defer()
            return

        # Get and validate configuration
        charm_config = CharmConfig.from_charm(self)
        errors = charm_config.validate()
        if errors:
            self.unit.status = ops.BlockedStatus(f"Config error: {errors[0]}")
            return

        # Generate and push configuration file
        self.unit.status = ops.MaintenanceStatus("configuring sungather")
        config_yaml = self._generate_config_yaml(charm_config)
        self.container.push(CONFIG_PATH, config_yaml, make_dirs=True)

        # Get secrets and update environment
        environment = self._get_environment(charm_config)

        # Add or update the Pebble layer
        layer = self._build_pebble_layer(charm_config, environment)
        self.container.add_layer(CONTAINER_NAME, layer, combine=True)

        # Restart the service to pick up changes
        try:
            if self.container.get_service(SERVICE_NAME).is_running():
                self.container.restart(SERVICE_NAME)
            else:
                self.container.start(SERVICE_NAME)
        except ops.pebble.ChangeError as e:
            logger.error("Failed to start service: %s", e)
            self.unit.status = ops.BlockedStatus(
                "service failed to start: check 'juju debug-log --include=sungather' "
                "for details, verify OCI image is correct"
            )
            return

        # Set workload version if available
        version = sungather.get_version(self.container)
        if version:
            self.unit.set_workload_version(version)

        self.unit.status = ops.ActiveStatus()

    def _build_pebble_layer(
        self, config: CharmConfig, environment: dict[str, str]
    ) -> ops.pebble.LayerDict:
        """Build the Pebble layer for SunGather."""
        command = f"/usr/bin/python3.10 sungather.py -c {CONFIG_PATH}"
        # Add PYTHONPATH to environment for rock-installed dependencies
        environment["PYTHONPATH"] = "/opt/sungather-lib"

        layer: ops.pebble.LayerDict = {
            "summary": "sungather layer",
            "description": "Pebble layer for SunGather",
            "services": {
                SERVICE_NAME: {
                    "override": "replace",
                    "summary": "SunGather data collection service",
                    "command": command,
                    "startup": "enabled",
                    "working-dir": "/opt/sungather/SunGather",
                    "environment": environment,
                }
            },
        }
        return layer

    def _generate_config_yaml(self, config: CharmConfig) -> str:  # noqa: C901
        """Generate the SunGather config.yaml content."""
        # Build the configuration dictionary
        config_dict: dict = {
            "inverter": {
                "host": config.inverter_host,
                "port": config.inverter_port,
                "connection": config.connection_type,
                "scan_interval": config.scan_interval,
                "level": config.level,
                "smart_meter": config.smart_meter,
            },
            "exports": [],
        }

        # Add model if specified
        if config.inverter_model:
            config_dict["inverter"]["model"] = config.inverter_model

        # Add webserver export
        if config.enable_webserver:
            config_dict["exports"].append(
                {"name": "webserver", "enabled": True, "port": config.webserver_port}
            )

        # Add MQTT export
        if config.enable_mqtt:
            mqtt_config = {
                "name": "mqtt",
                "enabled": True,
                "host": config.mqtt_host,
                "port": config.mqtt_port,
                "topic": config.mqtt_topic,
            }
            # Add username/password from secrets if available
            try:
                mqtt_username = self.model.get_secret(label="mqtt-username")
                mqtt_config["username"] = mqtt_username.get_content()["value"]
            except ops.SecretNotFoundError:
                pass

            try:
                mqtt_password = self.model.get_secret(label="mqtt-password")
                mqtt_config["password"] = mqtt_password.get_content()["value"]
            except ops.SecretNotFoundError:
                pass

            if config.mqtt_homeassistant:
                mqtt_config["homeassistant"] = True

            config_dict["exports"].append(mqtt_config)

        # Add InfluxDB export
        if config.enable_influxdb:
            influxdb_config = {
                "name": "influxdb",
                "enabled": True,
                "host": config.influxdb_host,
                "port": config.influxdb_port,
                "database": config.influxdb_database,
                "version": config.influxdb_version,
            }
            # Add token from secrets if available
            try:
                influxdb_token = self.model.get_secret(label="influxdb-token")
                influxdb_config["token"] = influxdb_token.get_content()["value"]
            except ops.SecretNotFoundError:
                pass

            config_dict["exports"].append(influxdb_config)

        # Add PVOutput export
        if config.pvoutput_enabled:
            pvoutput_config = {"name": "pvoutput", "enabled": True}
            # Add API key and system ID from secrets
            try:
                pvoutput_api_key = self.model.get_secret(label="pvoutput-api-key")
                pvoutput_config["api_key"] = pvoutput_api_key.get_content()["value"]
            except ops.SecretNotFoundError:
                pass

            try:
                pvoutput_system_id = self.model.get_secret(label="pvoutput-system-id")
                pvoutput_config["system_id"] = pvoutput_system_id.get_content()["value"]
            except ops.SecretNotFoundError:
                pass

            config_dict["exports"].append(pvoutput_config)

        return yaml.dump(config_dict, default_flow_style=False)

    def _get_environment(self, config: CharmConfig) -> dict[str, str]:
        """Get environment variables for the SunGather service."""
        # Map log levels to Python logging levels
        log_level_map = {
            "DEBUG": "10",
            "INFO": "20",
            "WARNING": "30",
            "ERROR": "40",
        }

        return {
            "TZ": "UTC",
            "LOG_LEVEL": log_level_map.get(config.log_level, "20"),
        }

    def _is_service_running(self) -> bool:
        """Check if the SunGather service is running."""
        try:
            service = self.container.get_service(SERVICE_NAME)
            return service.is_running()
        except (ops.ModelError, ops.pebble.ConnectionError):
            return False

    def _on_run_once_action(self, event: ops.ActionEvent) -> None:
        """Handle the run-once action."""
        if not self.container.can_connect():
            event.fail("Container is not ready")
            return

        try:
            # Run sungather with --runonce flag
            process = self.container.exec(
                [
                    "/usr/bin/python3.10",
                    "sungather.py",
                    "-c",
                    CONFIG_PATH,
                    "--runonce",
                ],
                timeout=60.0,
                encoding="utf-8",
                working_dir="/opt/sungather/SunGather",
                environment={"PYTHONPATH": "/opt/sungather-lib"},
            )
            stdout, stderr = process.wait_output()
            event.set_results({"output": stdout, "error": stderr if stderr else ""})
        except ops.pebble.ExecError as e:
            event.fail(f"Failed to run sungather: {e}")

    def _on_get_inverter_info_action(self, event: ops.ActionEvent) -> None:
        """Handle the get-inverter-info action."""
        if not self.container.can_connect():
            event.fail("Container is not ready")
            return

        try:
            info = sungather.get_inverter_info(self.container, CONFIG_PATH)
            event.set_results(info)
        except Exception as e:
            event.fail(f"Failed to get inverter info: {e}")

    def _on_test_connection_action(self, event: ops.ActionEvent) -> None:
        """Handle the test-connection action."""
        if not self.container.can_connect():
            event.fail("Container is not ready")
            return

        try:
            result = sungather.test_connection(self.container, CONFIG_PATH)
            event.set_results(result)
        except Exception as e:
            event.fail(f"Failed to test connection: {e}")


if __name__ == "__main__":  # pragma: nocover
    ops.main(SungatherCharm)
