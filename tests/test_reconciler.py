from unittest.mock import MagicMock, patch

import pytest

from src.models.manifest import ServiceManifest, VolumeSpec
from src.models.service import ClusterState, ContainerState
from src.models.state import StateLabel, SystemState
from src.reconciler.controller import (
    FailureStateError,
    IllegalTransitionError,
    reconcile,
)
from src.reconciler.model import ReconcilerConfig
from src.reconciler.observer import Observer
from src.reconciler.transitions import build_transition_map


def _noop_runner(state: StateLabel) -> None:
    """No-op command runner for tests that don't exercise command execution.

    Accepts a StateLabel argument (required by the CommandRunner protocol) and
    intentionally does nothing — used wherever tests verify control flow rather
    than subprocess dispatch.
    """


def _config(retries: int = 10) -> ReconcilerConfig:
    return ReconcilerConfig(
        desired_state=StateLabel.T5,
        transition_map=build_transition_map(),
        max_retries=retries,
        dry_run=False,
    )


def _observer_returning(label: StateLabel) -> MagicMock:
    obs = MagicMock()
    obs.observe.return_value = SystemState.from_label(label)
    return obs


# --- Transition map completeness ---


def test_transition_map_all_t_states() -> None:
    tm = build_transition_map()
    expected = [
        (StateLabel.T0, StateLabel.T1),
        (StateLabel.T1, StateLabel.T2),
        (StateLabel.T2, StateLabel.T3),
        (StateLabel.T3, StateLabel.T4),
        (StateLabel.T4, StateLabel.T5),
    ]
    for src, dst in expected:
        assert tm.transitions[src][0] == dst


def test_transition_map_f_states_recover_to_t0() -> None:
    tm = build_transition_map()
    for f in [
        StateLabel.F1,
        StateLabel.F2,
        StateLabel.F3,
        StateLabel.F4,
        StateLabel.F5,
    ]:
        assert tm.transitions[f] == [StateLabel.T0]


# --- Reconciler error paths ---


def test_reconcile_halts_on_failure_state() -> None:
    obs = _observer_returning(StateLabel.F1)
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        pytest.raises(FailureStateError, match="failure state F1"),
    ):
        reconcile(StateLabel.T5, _config(), [], _noop_runner)


def test_reconcile_exhausts_retries() -> None:
    obs = _observer_returning(StateLabel.T0)  # never advances
    mock_runner = MagicMock()
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        pytest.raises(RuntimeError, match="Max retries"),
    ):
        reconcile(StateLabel.T5, _config(retries=3), [], mock_runner)


def test_reconcile_no_transition_path() -> None:
    """T5 observed, desired=T3: T5 can only go to T0, not toward T3 → IllegalTransitionError."""
    cfg = ReconcilerConfig(
        desired_state=StateLabel.T3,
        transition_map=build_transition_map(),
        max_retries=5,
        dry_run=False,
    )
    obs = _observer_returning(StateLabel.T5)
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        pytest.raises(IllegalTransitionError, match="No legal path"),
    ):
        reconcile(StateLabel.T3, cfg, [], _noop_runner)


def test_reconcile_loop_terminates() -> None:
    """Reconciler exits immediately when observer already reports desired state."""
    config = ReconcilerConfig(
        desired_state=StateLabel.T5,
        transition_map=build_transition_map(),
        max_retries=10,
        dry_run=False,
    )
    obs = _observer_returning(StateLabel.T5)
    with patch("src.reconciler.controller.Observer", return_value=obs):
        reconcile(StateLabel.T5, config, [], _noop_runner)


def test_reconcile_dry_run_skips_commands() -> None:
    """dry_run=True advances state tracking without issuing any commands."""
    cfg = ReconcilerConfig(
        desired_state=StateLabel.T5,
        transition_map=build_transition_map(),
        max_retries=10,
        dry_run=True,
    )
    obs = _observer_returning(StateLabel.T5)
    mock_runner = MagicMock()
    with patch("src.reconciler.controller.Observer", return_value=obs):
        reconcile(StateLabel.T5, cfg, [], mock_runner)
    mock_runner.assert_not_called()


# --- Typed exception tests ---


def test_failure_state_error_is_runtime_error() -> None:
    assert issubclass(FailureStateError, RuntimeError)


def test_illegal_transition_error_is_value_error() -> None:
    assert issubclass(IllegalTransitionError, ValueError)


@pytest.mark.parametrize(
    "failure_state",
    [StateLabel.F1, StateLabel.F2, StateLabel.F3, StateLabel.F4, StateLabel.F5],
)
def test_all_failure_states_raise_failure_state_error(
    failure_state: StateLabel,
) -> None:
    obs = _observer_returning(failure_state)
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        pytest.raises(FailureStateError, match=failure_state),
    ):
        reconcile(StateLabel.T5, _config(), [], _noop_runner)


# --- Observer unit tests ---

_MANIFEST = ServiceManifest(
    service="baikal",
    uid=1001,
    user="svc_baikal",
    volumes=[VolumeSpec(name="cfg", path="/srv/baikal/config", mode="0750")],
)


def test_observer_t0_when_volumes_missing() -> None:
    with (
        patch("src.reconciler.observer._check_volumes", return_value=False),
        patch(
            "src.reconciler.observer._get_cluster_state",
            return_value=ClusterState(containers=[]),
        ),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T0


def test_observer_t1_when_permissions_wrong() -> None:
    with (
        patch("src.reconciler.observer._check_volumes", return_value=True),
        patch("src.reconciler.observer._check_permissions", return_value=False),
        patch(
            "src.reconciler.observer._get_cluster_state",
            return_value=ClusterState(containers=[]),
        ),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T1


def test_observer_t2_when_compose_not_running() -> None:
    with (
        patch("src.reconciler.observer._check_volumes", return_value=True),
        patch("src.reconciler.observer._check_permissions", return_value=True),
        patch(
            "src.reconciler.observer._get_cluster_state",
            return_value=ClusterState(containers=[]),
        ),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T2


def test_observer_t3_when_partially_running() -> None:
    cluster = ClusterState(
        containers=[
            ContainerState(service="baikal", running=True),
            ContainerState(service="jellyfin", running=False),
        ]
    )
    with (
        patch("src.reconciler.observer._check_volumes", return_value=True),
        patch("src.reconciler.observer._check_permissions", return_value=True),
        patch("src.reconciler.observer._get_cluster_state", return_value=cluster),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T3


def test_observer_t5_when_all_healthy() -> None:
    cluster = ClusterState(
        containers=[ContainerState(service="baikal", running=True, healthy=True)]
    )
    with (
        patch("src.reconciler.observer._check_volumes", return_value=True),
        patch("src.reconciler.observer._check_permissions", return_value=True),
        patch("src.reconciler.observer._get_cluster_state", return_value=cluster),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T5


def test_observer_t5_when_no_healthcheck() -> None:
    """Containers without healthchecks (healthy=None) are treated as healthy."""
    cluster = ClusterState(
        containers=[ContainerState(service="baikal", running=True, healthy=None)]
    )
    with (
        patch("src.reconciler.observer._check_volumes", return_value=True),
        patch("src.reconciler.observer._check_permissions", return_value=True),
        patch("src.reconciler.observer._get_cluster_state", return_value=cluster),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T5


def test_observer_t4_when_health_check_failing() -> None:
    cluster = ClusterState(
        containers=[ContainerState(service="baikal", running=True, healthy=False)]
    )
    with (
        patch("src.reconciler.observer._check_volumes", return_value=True),
        patch("src.reconciler.observer._check_permissions", return_value=True),
        patch("src.reconciler.observer._get_cluster_state", return_value=cluster),
    ):
        state = Observer().observe([_MANIFEST])
    assert state.label == StateLabel.T4


# --- Executor unit tests ---


def test_executor_run_command_calls_subprocess_for_known_state() -> None:
    """run_command dispatches a subprocess call for states with mapped commands."""
    from src.utils.executor import run_command

    with patch("src.utils.executor.subprocess.run") as mock_run:
        run_command(StateLabel.T1)
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "ansible-playbook" in cmd
    assert "--tags" in cmd
    assert "volumes" in cmd


def test_executor_run_command_noop_for_unmapped_state() -> None:
    """run_command does nothing for states without a mapped command (e.g. T0, T4, T5)."""
    from src.utils.executor import run_command

    with patch("src.utils.executor.subprocess.run") as mock_run:
        run_command(StateLabel.T0)
        run_command(StateLabel.T4)
        run_command(StateLabel.T5)
    mock_run.assert_not_called()


def test_reconcile_runner_called_on_advance() -> None:
    """reconcile() passes each next-state to the run_command callable when not dry_run."""
    states = [
        SystemState.from_label(StateLabel.T0),
        SystemState.from_label(StateLabel.T1),
        SystemState.from_label(StateLabel.T2),
        SystemState.from_label(StateLabel.T3),
        SystemState.from_label(StateLabel.T4),
        SystemState.from_label(StateLabel.T5),
    ]
    obs = MagicMock()
    obs.observe.side_effect = states
    mock_runner = MagicMock()
    with patch("src.reconciler.controller.Observer", return_value=obs):
        reconcile(StateLabel.T5, _config(retries=10), [], mock_runner)
    assert mock_runner.call_count == 5
    called_states = [call.args[0] for call in mock_runner.call_args_list]
    assert called_states == [
        StateLabel.T1,
        StateLabel.T2,
        StateLabel.T3,
        StateLabel.T4,
        StateLabel.T5,
    ]
