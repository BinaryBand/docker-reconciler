"""Manifest models for the docker-reconciler application."""

from typing import Any

from pydantic import BaseModel, field_validator


class VolumeSpec(BaseModel):
    """Specifies a volume mount configuration."""

    name: str
    path: str
    mode: str

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v: str) -> str:
        """Validates that the mode is a valid octal string."""
        if not v.startswith("0") or not all(c in "01234567" for c in v[1:]):
            raise ValueError(f"invalid octal mode: {v}")
        return v


class ServiceManifest(BaseModel):
    """Represents a service manifest configuration."""

    service: str
    uid: int
    user: str
    volumes: list[VolumeSpec]
    read_access: list[str] = []

    @field_validator("read_access")
    @classmethod
    def no_self_reference(cls, v: list[str], info: Any) -> list[str]:
        """Validates that a service does not grant read access to itself."""
        # Access the 'service' field from the validation context
        user = info.data.get("user")
        if user and user in v:
            raise ValueError(f"service cannot grant read access to itself: {user}")
        return v
