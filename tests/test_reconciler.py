from src.models.manifest import ServiceManifest, VolumeSpec
from src.models.state import StateLabel
from src.reconciler.controller import reconcile
from src.reconciler.model import ReconcilerConfig
from src.reconciler.transitions import build_transition_map


def test_transition_map() -> None:
    tm = build_transition_map()
    assert tm[StateLabel.T0] == StateLabel.T1
    assert tm[StateLabel.T4] == StateLabel.T5
    assert StateLabel.F1 not in tm


def test_reconcile_loop_terminates() -> None:
    config = ReconcilerConfig(desired_state=StateLabel.T5, max_retries=10, dry_run=False)
    manifests = [
        ServiceManifest(
            service="web",
            uid=1001,
            user="svc_web",
            volumes=[VolumeSpec(name="data", path="/data", mode="0750")],
        )
    ]
    reconcile(StateLabel.T5, config, manifests)
