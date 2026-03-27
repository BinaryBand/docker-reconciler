"""Utility functions for validating service manifests."""

from src.models.contract import ContractViolation, ValidationResult
from src.models.manifest import ServiceManifest


def _check_service(
    m: ServiceManifest, uids: set[int], volume_paths: set[str]
) -> list[ContractViolation]:
    violations: list[ContractViolation] = []
    if m.uid in uids:
        violations.append(
            ContractViolation(
                service=m.service, field="uid", message=f"duplicate UID: {m.uid}"
            )
        )
    uids.add(m.uid)
    for v in m.volumes:
        if v.path in volume_paths:
            violations.append(
                ContractViolation(
                    service=m.service,
                    field="volumes",
                    message=f"duplicate volume path: {v.path}",
                )
            )
        volume_paths.add(v.path)
    return violations


def validate_manifest(manifests: list[ServiceManifest]) -> ValidationResult:
    """Validates service manifests for consistency and duplicates."""
    errors: list[ContractViolation] = []
    uids: set[int] = set()
    volume_paths: set[str] = set()
    for m in manifests:
        errors.extend(_check_service(m, uids, volume_paths))
    return ValidationResult(valid=len(errors) == 0, errors=errors)
