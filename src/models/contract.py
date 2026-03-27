"""Models for the docker-reconciler application."""

from pydantic import BaseModel


class ContractViolation(BaseModel):
    """Represents a violation of the service contract."""

    service: str
    field: str
    message: str


class ValidationResult(BaseModel):
    """Represents the result of a contract validation."""

    valid: bool
    errors: list[ContractViolation]
