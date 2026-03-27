"""Models for the reconciler configuration."""

from pydantic import BaseModel

from src.models.state import StateLabel, TransitionMap


class ReconcilerConfig(BaseModel):
    """Configuration settings for the reconciliation process."""

    desired_state: StateLabel
    transition_map: TransitionMap
    max_retries: int
    dry_run: bool
