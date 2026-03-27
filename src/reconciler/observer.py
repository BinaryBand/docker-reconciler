"""Observer for monitoring actual system state via filesystem and Docker Compose."""

import stat
import subprocess
from pathlib import Path

from pydantic import BaseModel, ValidationError

from src.models.manifest import ServiceManifest
from src.models.service import ClusterState, ContainerState
from src.models.state import StateLabel, SystemState


class _ComposeContainer(BaseModel):
    """Raw shape of one docker compose ps --format json line."""

    Service: str
    State: str
    Health: str = ""
    ExitCode: int | None = None


def _check_volumes(manifests: list[ServiceManifest]) -> bool:
    return all(Path(vol.path).exists() for m in manifests for vol in m.volumes)


def _path_has_correct_uid(path: Path, uid: int) -> bool:
    return path.stat().st_uid == uid


def _path_has_correct_mode(path: Path, mode: str) -> bool:
    return stat.S_IMODE(path.stat().st_mode) == int(mode, 8)


def _volume_ok(path: Path, uid: int, mode: str) -> bool:
    if not path.exists():
        return False
    return _path_has_correct_uid(path, uid) and _path_has_correct_mode(path, mode)


def _check_permissions(manifests: list[ServiceManifest]) -> bool:
    return all(
        _volume_ok(Path(vol.path), m.uid, vol.mode)
        for m in manifests
        for vol in m.volumes
    )


def _to_container_state(raw: _ComposeContainer) -> ContainerState:
    healthy: bool | None = None
    if raw.Health == "healthy":
        healthy = True
    elif raw.Health == "unhealthy":
        healthy = False
    return ContainerState(
        service=raw.Service,
        running=raw.State == "running",
        healthy=healthy,
        exit_code=raw.ExitCode,
    )


def _parse_line(line: str) -> ContainerState | None:
    try:
        return _to_container_state(_ComposeContainer.model_validate_json(line))
    except ValidationError:
        return None


def _parse_compose_output(output: str) -> list[ContainerState]:
    containers: list[ContainerState] = []
    for line in output.strip().splitlines():
        container = _parse_line(line.strip())
        if container is not None:
            containers.append(container)
    return containers


def _get_cluster_state(manifests: list[ServiceManifest]) -> ClusterState:
    result = subprocess.run(
        ["docker", "compose", "ps", "--format", "json"],
        capture_output=True,
        text=True,
    )
    service_names = {m.service for m in manifests}
    containers = [
        c for c in _parse_compose_output(result.stdout) if c.service in service_names
    ]
    return ClusterState(containers=containers)


def _any_running(cluster: ClusterState) -> bool:
    return any(c.running for c in cluster.containers)


def _all_healthy_or_no_check(cluster: ClusterState) -> bool:
    return all(c.healthy is True or c.healthy is None for c in cluster.containers)


def _running_label(cluster: ClusterState) -> StateLabel:
    if not _any_running(cluster):
        return StateLabel.T2
    if not cluster.all_running():
        return StateLabel.T3
    if not _all_healthy_or_no_check(cluster):
        return StateLabel.T4
    return StateLabel.T5


def _derive_label(
    volumes: bool,
    permissions: bool,
    cluster: ClusterState,
) -> StateLabel:
    if not volumes:
        return StateLabel.T0
    if not permissions:
        return StateLabel.T1
    return _running_label(cluster)


class Observer:
    """Observes actual system state via filesystem and Docker Compose."""

    def observe(self, manifests: list[ServiceManifest]) -> SystemState:
        """Return the current observed system state."""
        volumes = _check_volumes(manifests)
        permissions = _check_permissions(manifests) if volumes else False
        cluster = _get_cluster_state(manifests)
        label = _derive_label(volumes, permissions, cluster)
        return SystemState.from_label(label)
