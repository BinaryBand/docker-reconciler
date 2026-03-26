from typing import Set, List
from src.models.manifest import ServiceManifest
from src.models.contract import ValidationResult, ContractViolation

def validate_manifest(manifests: List[ServiceManifest]) -> ValidationResult:
    errors: List[ContractViolation] = []
    uids: Set[int] = set()
    volume_paths: Set[str] = set()
    
    for m in manifests:
        if m.uid in uids:
            errors.append(ContractViolation(service=m.service, field="uid", message=f"duplicate UID: {m.uid}"))
        uids.add(m.uid)
        
        for v in m.volumes:
            if v.path in volume_paths:
                errors.append(ContractViolation(service=m.service, field="volumes", message=f"duplicate volume path: {v.path}"))
            volume_paths.add(v.path)
            
    return ValidationResult(valid=len(errors) == 0, errors=errors)
