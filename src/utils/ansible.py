from pydantic import BaseModel
from src.models.manifest import ServiceManifest

class AnsibleInventory(BaseModel):
    # Stub for inventory structure
    hosts: dict[str, str]

def load_inventory(path: str) -> AnsibleInventory:
    # Stub: return empty inventory
    return AnsibleInventory(hosts={})

def load_manifests(dir: str) -> list[ServiceManifest]:
    # Stub: return empty list
    return []
