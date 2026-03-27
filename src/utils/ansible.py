from pathlib import Path
from typing import Any, cast

import yaml

from src.models.manifest import ServiceManifest


class AnsibleHost:
    def __init__(self, ansible_host: str, ansible_user: str | None = None) -> None:
        self.ansible_host = ansible_host
        self.ansible_user = ansible_user


class AnsibleInventory:
    def __init__(
        self,
        hosts: dict[str, AnsibleHost] | None = None,
        vars: dict[str, str] | None = None,
    ) -> None:
        self.hosts = hosts or {}
        self.vars = vars or {}


def load_inventory(path: str) -> AnsibleInventory:
    return AnsibleInventory(hosts={})


def load_manifests(dir_path: str) -> list[ServiceManifest]:
    manifests: list[ServiceManifest] = []
    for path in Path(dir_path).glob("*.yml"):
        with path.open() as f:
            data: Any = yaml.safe_load(f)
            if isinstance(data, list):
                for item in cast(list[Any], data):
                    if isinstance(item, dict):
                        manifests.append(ServiceManifest(**cast(dict[str, Any], item)))
            elif isinstance(data, dict):
                manifests.append(ServiceManifest(**cast(dict[str, Any], data)))
    return manifests
