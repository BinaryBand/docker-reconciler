"""Ansible inventory models."""

from pydantic import BaseModel


class AnsibleHost(BaseModel):
    """Represents an Ansible host configuration."""

    ansible_host: str
    ansible_user: str | None = None


class AnsibleInventory(BaseModel):
    """Represents an Ansible inventory."""

    hosts: dict[str, AnsibleHost] = {}
    vars: dict[str, str] = {}
