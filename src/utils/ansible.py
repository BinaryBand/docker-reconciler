"""Utility functions for Ansible interactions."""

from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import BaseModel

from src.models.manifest import ServiceManifest


class AnsibleHost(BaseModel):
    """Represents an Ansible host configuration."""

    ansible_host: str
    ansible_user: str | None = None


class AnsibleInventory(BaseModel):
    """Represents an Ansible inventory."""

    hosts: dict[str, AnsibleHost] = {}
    vars: dict[str, str] = {}


def load_inventory(path: str) -> AnsibleInventory:
    """Loads an Ansible inventory from a file."""
    return AnsibleInventory(hosts={})


def load_manifests(dir_path: str) -> list[ServiceManifest]:
    """Loads all service manifests from a directory."""
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
