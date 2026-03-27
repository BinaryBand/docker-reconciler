"""Utility functions for Ansible interactions."""

from pathlib import Path
from typing import Any, cast

import yaml

from src.models.ansible import AnsibleInventory
from src.models.manifest import ServiceManifest


def load_inventory(path: str) -> AnsibleInventory:
    """Loads an Ansible inventory from a file."""
    return AnsibleInventory(hosts={})


def _items_from_yaml(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [item for item in cast(list[Any], data) if isinstance(item, dict)]
    if isinstance(data, dict):
        return [cast(dict[str, Any], data)]
    return []


def load_manifests(dir_path: str) -> list[ServiceManifest]:
    """Loads all service manifests from a directory."""
    manifests: list[ServiceManifest] = []
    for path in Path(dir_path).glob("*.yml"):
        with path.open() as f:
            for item in _items_from_yaml(yaml.safe_load(f)):
                manifests.append(ServiceManifest(**item))
    return manifests
