"""Models representing system states and transitions."""

from enum import StrEnum

from pydantic import BaseModel


class StateLabel(StrEnum):
    """Enumeration of system state labels."""

    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"
    F1 = "F1"
    F2 = "F2"
    F3 = "F3"
    F4 = "F4"
    F5 = "F5"


class SystemState(BaseModel):
    """Represents a snapshot of the system state."""

    label: StateLabel
    volumes: bool = False
    permissions: bool = False
    compose: bool = False
    post_start: bool = False
    health: bool = False

    @classmethod
    def from_label(cls, label: StateLabel) -> "SystemState":
        """Creates a SystemState instance from a StateLabel."""
        return cls(
            label=label,
            volumes=label
            in [
                StateLabel.T1,
                StateLabel.T2,
                StateLabel.T3,
                StateLabel.T4,
                StateLabel.T5,
            ],
            permissions=label
            in [StateLabel.T2, StateLabel.T3, StateLabel.T4, StateLabel.T5],
            compose=label in [StateLabel.T3, StateLabel.T4, StateLabel.T5],
            post_start=label in [StateLabel.T4, StateLabel.T5],
            health=label == StateLabel.T5,
        )


class TransitionMap(BaseModel):
    """Defines valid state transitions."""

    transitions: dict[StateLabel, list[StateLabel]] = {
        StateLabel.T0: [StateLabel.T1],
        StateLabel.T1: [StateLabel.T2, StateLabel.F1, StateLabel.T0],
        StateLabel.T2: [StateLabel.T3, StateLabel.F2, StateLabel.T0],
        StateLabel.T3: [StateLabel.T4, StateLabel.F3, StateLabel.T0],
        StateLabel.T4: [StateLabel.T5, StateLabel.F4, StateLabel.T0],
        StateLabel.T5: [StateLabel.T0],
        StateLabel.F1: [StateLabel.T0],
        StateLabel.F2: [StateLabel.T0],
        StateLabel.F3: [StateLabel.T0],
        StateLabel.F4: [StateLabel.T0],
        StateLabel.F5: [StateLabel.T0],
    }

    def _forward_neighbors(self, current: StateLabel) -> list[StateLabel]:
        return [
            s
            for s in self.transitions.get(current, [])
            if not s.startswith("F") and s != StateLabel.T0
        ]

    def is_legal_transition(
        self, from_state: StateLabel, to_state: StateLabel
    ) -> bool:
        """Returns True if transitioning from from_state to to_state is permitted."""
        return to_state in self.transitions.get(from_state, [])

    def next_toward(
        self, current: StateLabel, desired: StateLabel
    ) -> StateLabel | None:
        """Determines the next state in a path toward the desired state."""
        legal = self.transitions.get(current, [])
        if desired in legal:
            return desired
        forward = self._forward_neighbors(current)
        return forward[0] if forward else None
