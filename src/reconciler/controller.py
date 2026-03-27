"""Reconciliation controller logic."""

from collections.abc import Callable

from src.models.manifest import ServiceManifest
from src.models.state import StateLabel
from src.reconciler.model import ReconcilerConfig
from src.reconciler.observer import Observer

CommandRunner = Callable[[StateLabel], None]


class FailureStateError(RuntimeError):
    """Raised when reconciliation encounters a failure state and must halt."""


class IllegalTransitionError(ValueError):
    """Raised when an attempted state transition is not permitted by the transition map."""


_FAILURE_STATES: frozenset[StateLabel] = frozenset(
    [StateLabel.F1, StateLabel.F2, StateLabel.F3, StateLabel.F4, StateLabel.F5]
)


def _advance(
    current: StateLabel,
    desired: StateLabel,
    config: ReconcilerConfig,
    run_command: CommandRunner,
) -> bool:
    """Advance one step toward desired. Returns True when desired is reached."""
    if current == desired:
        return True
    if current in _FAILURE_STATES:
        raise FailureStateError(
            f"Reconciliation halted: system is in failure state {current}"
        )
    next_state = config.transition_map.next_toward(current, desired)
    if next_state is None:
        raise IllegalTransitionError(f"No legal path from {current} to {desired}")
    if not config.dry_run:
        run_command(next_state)
    return False


def reconcile(
    desired: StateLabel,
    config: ReconcilerConfig,
    manifests: list[ServiceManifest],
    run_command: CommandRunner,
) -> None:
    """Run reconciliation loop until desired state is reached or retries exhausted."""
    observer = Observer()
    for _ in range(config.max_retries):
        current = observer.observe(manifests)
        print(f"Current state: {current.label}, Desired: {desired}")
        if _advance(current.label, desired, config, run_command):
            print("Desired state reached.")
            return
    raise RuntimeError("Max retries exceeded")
