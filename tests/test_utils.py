from src.models.manifest import ServiceManifest, VolumeSpec
from src.utils.validate_manifest import validate_manifest


def test_validate_manifest_duplicates():
    v1 = VolumeSpec(name="data1", path="/srv/data", mode="0750")
    m1 = ServiceManifest(service="baikal", uid=1000, user="svc_baikal", volumes=[v1])
    m2 = ServiceManifest(service="jellyfin", uid=1000, user="svc_jellyfin", volumes=[])

    result = validate_manifest([m1, m2])
    assert result.valid is False
    assert any(e.field == "uid" for e in result.errors)


def test_validate_manifest_volume_path_duplicate():
    v1 = VolumeSpec(name="data1", path="/srv/data", mode="0750")
    v2 = VolumeSpec(name="data2", path="/srv/data", mode="0750")
    m1 = ServiceManifest(service="baikal", uid=1000, user="svc_baikal", volumes=[v1])
    m2 = ServiceManifest(
        service="jellyfin", uid=1001, user="svc_jellyfin", volumes=[v2]
    )

    result = validate_manifest([m1, m2])
    assert result.valid is False
    assert any(e.field == "volumes" for e in result.errors)


def test_validate_manifest_empty_list() -> None:
    assert validate_manifest([]).valid is True


def test_validate_manifest_single_service() -> None:
    m = ServiceManifest(
        service="baikal",
        uid=1001,
        user="svc_baikal",
        volumes=[VolumeSpec(name="cfg", path="/srv/baikal/config", mode="0750")],
    )
    assert validate_manifest([m]).valid is True


def test_validate_manifest_all_unique() -> None:
    """Migrated service shapes (baikal/jellyfin/restic) pass the T0 gate."""
    baikal = ServiceManifest(
        service="baikal",
        uid=1001,
        user="svc_baikal",
        volumes=[VolumeSpec(name="cfg", path="/srv/baikal/config", mode="0750")],
    )
    jellyfin = ServiceManifest(
        service="jellyfin",
        uid=1000,
        user="svc_jellyfin",
        volumes=[VolumeSpec(name="media", path="/srv/media", mode="0755")],
    )
    restic = ServiceManifest(
        service="restic",
        uid=1002,
        user="svc_restic",
        volumes=[VolumeSpec(name="repo", path="/srv/restic/repo", mode="0700")],
    )
    result = validate_manifest([baikal, jellyfin, restic])
    assert result.valid is True
    assert result.errors == []
