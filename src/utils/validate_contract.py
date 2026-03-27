import sys
from pathlib import Path

import yaml

from src.models.contract import ContractViolation, ValidationResult
from src.models.manifest import ServiceManifest


def _load_compose(compose_path: str) -> dict:
    with Path(compose_path).open() as f:
        return yaml.safe_load(f).get("services", {})


def validate_contract(
    manifests: list[ServiceManifest], compose_path: str
) -> ValidationResult:
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

        if "user" in c and str(c["user"]) != str(svc.uid):
            violations.append(
                ContractViolation(
                    service=svc.service,
                    field="uid",
                    message=f"UID mismatch: expected {svc.uid}, got {c['user']}",
                )
            )

        declared_mounts = [v.split(":")[0] for v in c.get("volumes", [])]
        for vol in svc.volumes:
            if vol.path not in declared_mounts:
                violations.append(
                    ContractViolation(
                        service=svc.service,
                        field="volumes",
                        message=f"volume '{vol.path}' not mounted in Compose",
                    )
                )

    return ValidationResult(valid=len(violations) == 0, errors=violations)


if __name__ == "__main__":
    from src.utils.ansible import load_manifests

    manifests = load_manifests("ansible/manifests")
    result = validate_contract(manifests, "docker-compose.yml")
    for e in result.errors:
        print(f"ERROR {e.service} [{e.field}]: {e.message}")
    sys.exit(0 if result.valid else 1)
