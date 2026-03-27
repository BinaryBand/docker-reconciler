import pytest

from src.models.manifest import ServiceManifest, VolumeSpec
from src.models.service import ClusterState, ContainerState
from src.models.state import StateLabel, SystemState, TransitionMap


def test_volume_spec_mode():
    v = VolumeSpec(name="data", path="/data", mode="0750")
    assert v.mode == "0750"
    with pytest.raises(ValueError):
        VolumeSpec(name="data", path="/data", mode="750")


def test_service_manifest_creation():
    m = ServiceManifest(
        service="baikal",
        uid=1000,
        user="svc_baikal",
        volumes=[
            VolumeSpec(name="config", path="/srv/baikal/config", mode="0750"),
            VolumeSpec(name="data", path="/srv/baikal/data", mode="0750"),
        ],
    )
    assert m.service == "baikal"
    assert len(m.volumes) == 2


def test_state_label():
    assert StateLabel.T0 == "T0"


def test_transition_map():
    tm = TransitionMap()
    assert tm.next_toward(StateLabel.T0, StateLabel.T1) == StateLabel.T1
    assert tm.next_toward(StateLabel.T0, StateLabel.T5) == StateLabel.T1


def test_cluster_state():
    cs = ClusterState(
        containers=[
            ContainerState(service="web", running=True, healthy=True, exit_code=0)
        ]
    )
    assert cs.all_running() is True
    assert cs.all_healthy() is True


# --- Failure-state labels ---


def test_failure_state_labels() -> None:
    for label in [
        StateLabel.F1,
        StateLabel.F2,
        StateLabel.F3,
        StateLabel.F4,
        StateLabel.F5,
    ]:
        assert label.value.startswith("F")


# --- SystemState.from_label step booleans ---


def test_system_state_t0_all_false() -> None:
    s = SystemState.from_label(StateLabel.T0)
    assert not any([s.volumes, s.permissions, s.compose, s.post_start, s.health])


def test_system_state_t5_all_true() -> None:
    s = SystemState.from_label(StateLabel.T5)
    assert all([s.volumes, s.permissions, s.compose, s.post_start, s.health])


def test_system_state_t3_partial() -> None:
    s = SystemState.from_label(StateLabel.T3)
    assert s.volumes and s.compose
    assert not s.post_start and not s.health


# --- VolumeSpec mode validator edge case ---


def test_volume_spec_invalid_chars() -> None:
    with pytest.raises(ValueError):
        VolumeSpec(name="x", path="/x", mode="0899")


# --- ServiceManifest read_access self-reference ---


def test_service_manifest_no_self_read_access() -> None:
    with pytest.raises(ValueError):
        ServiceManifest(
            service="baikal",
            uid=1001,
            user="svc_baikal",
            volumes=[],
            read_access=["svc_baikal"],
        )


# --- ClusterState edge cases ---


def test_cluster_state_mixed_running() -> None:
    cs = ClusterState(
        containers=[
            ContainerState(service="a", running=True, healthy=True, exit_code=0),
            ContainerState(service="b", running=False, healthy=False, exit_code=1),
        ]
    )
    assert cs.all_running() is False
    assert cs.all_healthy() is False


def test_cluster_state_empty() -> None:
    # Python's all() on an empty iterable returns True — document this behaviour.
    cs = ClusterState(containers=[])
    assert cs.all_running() is True
    assert cs.all_healthy() is True
