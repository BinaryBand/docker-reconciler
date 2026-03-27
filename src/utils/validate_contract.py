"""Utility functions for validating service contracts."""

import sys
from pathlib import Path

import yaml

from src.models.contract import (
    ComposeFile,
    ComposeService,
    ContractViolation,
    ValidationResult,
)
from src.models.manifest import ServiceManifest


def _load_compose(compose_path: str) -> dict[str, ComposeService]:
    """Loads a docker-compose.yml file."""
    with Path(compose_path).open() as f:
        return ComposeFile.model_validate(yaml.safe_load(f)).services


def _check_uid(
    svc: ServiceManifest, c: ComposeService, violations: list[ContractViolation]
) -> None:
    if c.user is not None and c.user.split(":")[0] != str(svc.uid):
        violations.append(
            ContractViolation(
                service=svc.service,
                field="uid",
                message=f"UID mismatch: expected {svc.uid}, got {c.user}",
            )
        )


def _get_declared_mounts(c: ComposeService) -> list[str]:
    return [v.split(":")[0] for v in c.volumes]


def _check_volumes(
    svc: ServiceManifest,
    declared_mounts: list[str],
    violations: list[ContractViolation],
) -> None:
    for vol in svc.volumes:
        if vol.path not in declared_mounts:
            violations.append(
                ContractViolation(
                    service=svc.service,
                    field="volumes",
                    message=f"volume '{vol.path}' not mounted in Compose",
                )
            )


def validate_contract(
    manifests: list[ServiceManifest], compose_path: str
) -> ValidationResult:
    """Validates the service contract against the docker-compose.yml."""
    violations: list[ContractViolation] = []
    compose = _load_compose(compose_path)

    for svc in manifests:
        if svc.service not in compose:
            violations.append(
                ContractViolation(
                    service=svc.service,
                    field="service",
                    message=f"service '{svc.service}' missing from Compose",
                )
            )
            continue
        c = compose[svc.service]
        _check_uid(svc, c, violations)
        _check_volumes(svc, _get_declared_mounts(c), violations)

    return ValidationResult(valid=len(violations) == 0, errors=violations)


if __name__ == "__main__":
    from src.utils.ansible import load_manifests

    manifests = load_manifests("ansible/manifests")
    result = validate_contract(manifests, "docker-compose.yml")
    for e in result.errors:
        print(f"ERROR {e.service} [{e.field}]: {e.message}")
    sys.exit(0 if result.valid else 1)
