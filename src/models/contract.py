"""Models for the docker-reconciler application."""

from typing import cast

from pydantic import BaseModel, ConfigDict, field_validator


class ContractViolation(BaseModel):
    """Represents a violation of the service contract."""

    service: str
    field: str
    message: str


class ValidationResult(BaseModel):
    """Represents the result of a contract validation."""

    valid: bool
    errors: list[ContractViolation]


class ComposeService(BaseModel):
    """Minimal docker-compose service entry for contract validation."""

    user: str | None = None
    volumes: list[str] = []
    model_config = ConfigDict(extra="allow")

    @field_validator("volumes", mode="before")
    @classmethod
    def keep_string_volumes(cls, v: object) -> list[str]:
        """Retain only string-form volume mounts; ignore long-form objects."""
        if not isinstance(v, list):
            return []
        items = cast(list[object], v)
        return [item for item in items if isinstance(item, str)]


class ComposeFile(BaseModel):
    """Minimal docker-compose file structure for contract validation."""

    services: dict[str, ComposeService] = {}
    model_config = ConfigDict(extra="allow")
