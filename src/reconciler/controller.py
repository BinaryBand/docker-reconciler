import time

from src.models.manifest import ServiceManifest
from src.models.state import StateLabel
from src.reconciler.model import ReconcilerConfig
from src.reconciler.observer import Observer
from src.reconciler.transitions import build_transition_map

_FAILURE_STATES: frozenset[StateLabel] = frozenset(
    [StateLabel.F1, StateLabel.F2, StateLabel.F3, StateLabel.F4, StateLabel.F5]
)


def issue_command(state: StateLabel) -> None:
    """Issue a command to advance the system toward the given state."""
    print(f"Executing command for state {state}")
    time.sleep(0.1)


def reconcile(
    desired: StateLabel, config: ReconcilerConfig, manifests: list[ServiceManifest]
) -> None:
    """
    Run the reconciliation loop until desired state is reached or retries exhausted.
    """
    transition_map = build_transition_map()
    observer = Observer()

    for _ in range(config.max_retries):
        current = observer.observe(manifests)
        print(f"Current state: {current.label}, Desired: {desired}")

        if current.label == desired:
            print("Desired state reached.")
            return

        if current.label in _FAILURE_STATES:
            raise RuntimeError(f"Reconciliation halted: {current.label}")

        next_state = transition_map.next_toward(current.label, desired)
        if next_state is None:
            raise RuntimeError(f"No path from {current.label} to {desired}")

        issue_command(next_state)

    raise RuntimeError("Max retries exceeded")
