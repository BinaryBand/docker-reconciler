import pytest
from src.models.manifest import VolumeSpec, ServiceManifest
from src.models.state import StateLabel, TransitionMap
from src.models.service import ClusterState, ContainerState

def test_volume_spec_mode():
    v = VolumeSpec(name="data", path="/data", mode="0750")
    assert v.mode == "0750"
    with pytest.raises(ValueError):
        VolumeSpec(name="data", path="/data", mode="750")

def test_service_manifest_self_reference():
    # This might need adjustment depending on how we want to test validator context
    # Just testing successful creation for now
    m = ServiceManifest(service="web", uid=1001, user="svc_web", volumes=[VolumeSpec(name="data", path="/data", mode="0750")])
    assert m.service == "web"

def test_state_label():
    assert StateLabel.T0 == "T0"

def test_transition_map():
    tm = TransitionMap()
    assert tm.next_toward(StateLabel.T0, StateLabel.T1) == StateLabel.T1
    assert tm.next_toward(StateLabel.T0, StateLabel.T0) is None

def test_cluster_state():
    cs = ClusterState(containers=[
        ContainerState(service="web", running=True, healthy=True, exit_code=0)
    ])
    assert cs.all_running() is True
    assert cs.all_healthy() is True
