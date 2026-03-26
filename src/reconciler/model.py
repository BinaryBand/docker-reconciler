from pydantic import BaseModel

from src.models.state import StateLabel

class ReconcilerConfig(BaseModel):
    desired_state: StateLabel
    max_retries: int
    dry_run: bool
