"""Service state models for the docker-reconciler application."""

from pydantic import BaseModel


class ContainerState(BaseModel):
    """Represents the state of a container."""

    service: str
    running: bool
    healthy: bool | None = None
    exit_code: int | None = None


class ClusterState(BaseModel):
    """Represents the state of a cluster of containers."""

    containers: list[ContainerState]

    def all_running(self) -> bool:
        """Checks if all containers are in the running state."""
        return all(c.running for c in self.containers)

    def all_healthy(self) -> bool:
        """Checks if all containers are healthy."""
        return all(c.healthy is True for c in self.containers)
