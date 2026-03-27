
from pydantic import BaseModel


class ContainerState(BaseModel):
    service: str
    running: bool
    healthy: bool | None = None
    exit_code: int | None = None

class ClusterState(BaseModel):
    containers: list[ContainerState]

    def all_running(self) -> bool:
        return all(c.running for c in self.containers)

    def all_healthy(self) -> bool:
        return all(c.healthy is True for c in self.containers)
