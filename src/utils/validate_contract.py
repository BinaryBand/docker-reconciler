from src.models.manifest import ServiceManifest
from src.models.contract import ValidationResult
from typing import List

def validate_contract(manifests: List[ServiceManifest], compose_path: str) -> ValidationResult:
    # Stub: always return valid for now
    return ValidationResult(valid=True, errors=[])
