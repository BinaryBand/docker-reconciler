from pathlib import Path

import yaml
from pydantic import BaseModel

from src.models.manifest import ServiceManifest


class AnsibleHost(BaseModel):
    ansible_host: str
    ansible_user: str | None = None


class AnsibleInventory(BaseModel):
    hosts: dict[str, AnsibleHost] = {}
    vars: dict[str, str] = {}


def load_inventory(path: str) -> AnsibleInventory:
    return AnsibleInventory(hosts={})


def load_manifests(dir: str) -> list[ServiceManifest]:
    manifests = []
    for path in Path(dir).glob("*.yml"):
        with path.open() as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                manifests.extend(ServiceManifest(**item) for item in data)
            else:
                manifests.append(ServiceManifest(**data))
    return manifests
