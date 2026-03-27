from unittest.mock import MagicMock, patch

import pytest

from src.models.manifest import ServiceManifest, VolumeSpec
from src.models.service import ClusterState, ContainerState
from src.models.state import StateLabel, SystemState
from src.reconciler.controller import reconcile
from src.reconciler.model import ReconcilerConfig
from src.reconciler.observer import Observer
from src.reconciler.transitions import build_transition_map


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
        pytest.raises(RuntimeError, match="Reconciliation halted"),
    ):
        reconcile(StateLabel.T5, _config(), [])


def test_reconcile_exhausts_retries() -> None:
    obs = _observer_returning(StateLabel.T0)  # never advances
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        patch("src.reconciler.controller.issue_command"),
        pytest.raises(RuntimeError, match="Max retries"),
    ):
        reconcile(StateLabel.T5, _config(retries=3), [])


def test_reconcile_no_transition_path() -> None:
    """T5 observed, desired=T3: T5 can only go to T0, not toward T3 → RuntimeError."""
    cfg = ReconcilerConfig(
        desired_state=StateLabel.T3,
        transition_map=build_transition_map(),
        max_retries=5,
        dry_run=False,
    )
    obs = _observer_returning(StateLabel.T5)
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        pytest.raises(RuntimeError, match="No path"),
    ):
        reconcile(StateLabel.T3, cfg, [])


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
        reconcile(StateLabel.T5, config, [])


def test_reconcile_dry_run_skips_commands() -> None:
    """dry_run=True advances state tracking without issuing any commands."""
    cfg = ReconcilerConfig(
        desired_state=StateLabel.T5,
        transition_map=build_transition_map(),
        max_retries=10,
        dry_run=True,
    )
    obs = _observer_returning(StateLabel.T5)
    with (
        patch("src.reconciler.controller.Observer", return_value=obs),
        patch("src.reconciler.controller.issue_command") as mock_cmd,
    ):
        reconcile(StateLabel.T5, cfg, [])
    mock_cmd.assert_not_called()


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
