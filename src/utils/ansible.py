"""Utility functions for Ansible interactions."""

import subprocess
from pathlib import Path
from typing import cast

import yaml
from pydantic import BaseModel, ConfigDict, Field

from src.models.ansible import AnsibleHost, AnsibleInventory
from src.models.manifest import ServiceManifest
from src.utils.types import is_str_dict


class _HostVars(BaseModel):
    ansible_host: str | None = None
    ansible_user: str | None = None
    model_config = ConfigDict(extra="allow")


class _Meta(BaseModel):
    hostvars: dict[str, _HostVars] = {}
    model_config = ConfigDict(extra="allow")


class _InventoryJSON(BaseModel):
    meta: _Meta = Field(default_factory=_Meta, alias="_meta")
    model_config = ConfigDict(extra="allow", populate_by_name=True)


def load_inventory(path: str) -> AnsibleInventory:
    """Loads an Ansible inventory by running ansible-inventory --list."""
    result = subprocess.run(
        ["ansible-inventory", "--list", "-i", path],
        capture_output=True,
        text=True,
        check=True,
    )
    parsed = _InventoryJSON.model_validate_json(result.stdout)
    hosts = {
        name: AnsibleHost(
            ansible_host=hv.ansible_host or name,
            ansible_user=hv.ansible_user,
        )
        for name, hv in parsed.meta.hostvars.items()
    }
    return AnsibleInventory(hosts=hosts)


def load_manifests(dir_path: str) -> list[ServiceManifest]:
    """Loads all service manifests from a directory."""
    manifests: list[ServiceManifest] = []
    for path in Path(dir_path).glob("*.yml"):
        with path.open() as f:
            data = yaml.safe_load(f)

        items = cast(list[object], data)
        manifests.extend(
            ServiceManifest.model_validate(item) for item in items if is_str_dict(item)
        )
    return manifests
