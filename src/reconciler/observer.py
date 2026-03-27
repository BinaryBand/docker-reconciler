from dataclasses import dataclass, field

from src.models.manifest import ServiceManifest
from src.models.state import StateLabel, SystemState

_SEQUENCE: list[StateLabel] = [
    StateLabel.T0,
    StateLabel.T1,
    StateLabel.T2,
    StateLabel.T3,
    StateLabel.T4,
    StateLabel.T5,
]


@dataclass
class Observer:
    """Simulated observer that advances through states on each call."""

    _index: int = field(default=0, init=False)

    def observe(self, manifests: list[ServiceManifest]) -> SystemState:
        """Return the current observed system state."""
        state = _SEQUENCE[min(self._index, len(_SEQUENCE) - 1)]
        self._index += 1
        return SystemState.from_label(state)
