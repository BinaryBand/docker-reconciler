from enum import Enum

from pydantic import BaseModel


class StateLabel(str, Enum):
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
    label: StateLabel
    steps: dict[str, bool]

    @classmethod
    def from_label(cls, label: StateLabel) -> "SystemState":
        return cls(
            label=label,
            steps={
                "provisioned": label in [StateLabel.T1, StateLabel.T2, StateLabel.T3, StateLabel.T4, StateLabel.T5],
                "configured": label in [StateLabel.T2, StateLabel.T3, StateLabel.T4, StateLabel.T5],
                "started": label in [StateLabel.T3, StateLabel.T4, StateLabel.T5],
                "hooked": label in [StateLabel.T4, StateLabel.T5],
                "healthy": label == StateLabel.T5,
            }
        )

class TransitionMap:
    def __init__(self):
        self._transitions: dict[StateLabel, StateLabel] = {
            StateLabel.T0: StateLabel.T1,
            StateLabel.T1: StateLabel.T2,
            StateLabel.T2: StateLabel.T3,
            StateLabel.T3: StateLabel.T4,
            StateLabel.T4: StateLabel.T5,
        }

    def next_toward(self, current: StateLabel, desired: StateLabel) -> StateLabel | None:
        if current == desired:
            return None
        return self._transitions.get(current)
