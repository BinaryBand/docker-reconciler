from src.models.state import StateLabel

def build_transition_map() -> dict[StateLabel, StateLabel]:
    return {
        StateLabel.T0: StateLabel.T1,
        StateLabel.T1: StateLabel.T2,
        StateLabel.T2: StateLabel.T3,
        StateLabel.T3: StateLabel.T4,
        StateLabel.T4: StateLabel.T5,
    }
