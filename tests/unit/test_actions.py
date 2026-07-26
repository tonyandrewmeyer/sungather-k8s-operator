# Copyright 2025 Ubuntu
# See LICENSE file for licensing details.
#
# State-transition tests for the charm actions, exercising both the action
# handlers in charm.py and the workload helpers in sungather.py.

import pytest
from ops import testing

from charm import CONTAINER_NAME, SungatherCharm

# The run-once and test-connection actions exec SunGather; match on the leading
# part of the command so the simulated container can answer.
RUNONCE_PREFIX = ["/usr/bin/python3.10", "sungather.py"]


def _run_action(name, *, can_connect=True, execs=()):
    ctx = testing.Context(SungatherCharm)
    container = testing.Container(CONTAINER_NAME, can_connect=can_connect, execs=set(execs))
    state_in = testing.State(containers={container}, config={"inverter-host": "192.168.1.100"})
    ctx.run(ctx.on.action(name), state_in)
    assert ctx.action_results is not None
    return ctx.action_results


@pytest.mark.parametrize("action", ["run-once", "get-inverter-info", "test-connection"])
def test_action_fails_when_container_not_ready(action):
    """Every action fails cleanly while the workload container is unreachable."""
    with pytest.raises(testing.ActionFailed) as exc:
        _run_action(action, can_connect=False)
    assert exc.value.message == "Container is not ready"


def test_run_once_returns_workload_output():
    """run-once returns the workload's stdout and stderr."""
    exec_ = testing.Exec(RUNONCE_PREFIX, stdout="collection complete\n", stderr="")
    results = _run_action("run-once", execs=[exec_])
    assert results["output"] == "collection complete\n"
    assert results["error"] == ""


def test_run_once_reports_exec_failure():
    """run-once fails the action when the workload exits non-zero."""
    exec_ = testing.Exec(RUNONCE_PREFIX, return_code=1, stdout="", stderr="boom")
    with pytest.raises(testing.ActionFailed):
        _run_action("run-once", execs=[exec_])


def test_get_inverter_info_reports_status():
    """get-inverter-info returns the charm's view of the inverter configuration."""
    results = _run_action("get-inverter-info")
    assert results["status"] == "Configuration loaded"
    assert results["config-path"] == "/config/config.yaml"


def test_test_connection_success():
    """test-connection reports success when the workload collects data cleanly."""
    exec_ = testing.Exec(RUNONCE_PREFIX, stdout="data collected\n", stderr="")
    results = _run_action("test-connection", execs=[exec_])
    assert results["status"] == "success"


def test_test_connection_detects_error_output():
    """test-connection reports failure when the workload emits an error."""
    exec_ = testing.Exec(RUNONCE_PREFIX, stdout="ERROR: cannot reach inverter\n", stderr="")
    results = _run_action("test-connection", execs=[exec_])
    assert results["status"] == "failed"


def test_test_connection_handles_exec_failure():
    """test-connection reports failure when the exec itself fails."""
    exec_ = testing.Exec(RUNONCE_PREFIX, return_code=1, stdout="", stderr="exec failed")
    results = _run_action("test-connection", execs=[exec_])
    assert results["status"] == "failed"
