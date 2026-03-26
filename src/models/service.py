from pydantic import BaseModel
from typing import List

class ContainerState(BaseModel):
    service: str
    running: bool
    healthy: bool
    exit_code: int

class ClusterState(BaseModel):
    containers: List[ContainerState]

    def all_running(self) -> bool:
        return all(c.running for c in self.containers)

    def all_healthy(self) -> bool:
        return all(c.healthy for c in self.containers)
