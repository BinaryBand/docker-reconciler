from src.utils.validate_manifest import validate_manifest
from src.models.manifest import ServiceManifest, VolumeSpec

def test_validate_manifest_duplicates():
    v1 = VolumeSpec(name="data1", path="/data", mode="0750")
    m1 = ServiceManifest(service="web1", uid=1001, user="svc_web", volumes=[v1])
    m2 = ServiceManifest(service="web2", uid=1001, user="svc_web", volumes=[])
    
    result = validate_manifest([m1, m2])
    assert result.valid is False
    assert any(e.field == "uid" for e in result.errors)

def test_validate_manifest_volume_path_duplicate():
    v1 = VolumeSpec(name="data1", path="/data", mode="0750")
    v2 = VolumeSpec(name="data2", path="/data", mode="0750")
    m1 = ServiceManifest(service="web1", uid=1001, user="svc_web", volumes=[v1])
    m2 = ServiceManifest(service="web2", uid=1002, user="svc_web", volumes=[v2])
    
    result = validate_manifest([m1, m2])
    assert result.valid is False
    assert any(e.field == "volumes" for e in result.errors)
