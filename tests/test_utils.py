import os
import tempfile

import pytest
import yaml

from src.models.manifest import ServiceManifest, VolumeSpec
from src.utils.validate_contract import validate_contract
from src.utils.validate_manifest import validate_manifest
from src.utils.validate_no_duplicates import validate


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


# --- validate_contract ---


def _write_compose(services: dict[str, object]) -> str:
    """Write a temporary docker-compose file and return its path."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yml", delete=False
    ) as f:
        yaml.dump({"services": services}, f)
        return f.name


def test_validate_contract_service_missing_from_compose() -> None:
    manifests = [
        ServiceManifest(service="missing", uid=1001, user="svc_missing", volumes=[])
    ]
    path = _write_compose({})
    try:
        result = validate_contract(manifests, path)
        assert result.valid is False
        assert any(e.field == "service" for e in result.errors)
    finally:
        os.unlink(path)


def test_validate_contract_uid_mismatch() -> None:
    manifests = [
        ServiceManifest(
            service="test",
            uid=1001,
            user="svc_test",
            volumes=[VolumeSpec(name="data", path="/srv/test", mode="0750")],
        )
    ]
    path = _write_compose({"test": {"user": "9999", "volumes": ["/srv/test:/data"]}})
    try:
        result = validate_contract(manifests, path)
        assert result.valid is False
        assert any(e.field == "uid" for e in result.errors)
    finally:
        os.unlink(path)


def test_validate_contract_volume_missing_from_compose() -> None:
    manifests = [
        ServiceManifest(
            service="test",
            uid=1001,
            user="svc_test",
            volumes=[VolumeSpec(name="data", path="/srv/test", mode="0750")],
        )
    ]
    path = _write_compose({"test": {"volumes": []}})
    try:
        result = validate_contract(manifests, path)
        assert result.valid is False
        assert any(e.field == "volumes" for e in result.errors)
    finally:
        os.unlink(path)


def test_validate_contract_passes_with_real_compose() -> None:
    """All three project manifests validate cleanly against docker-compose.yml."""
    from src.utils.ansible import load_manifests

    manifests = load_manifests("ansible/manifests")
    result = validate_contract(manifests, "docker-compose.yml")
    assert result.valid is True


# --- validate_no_duplicates ---


def test_validate_no_duplicates_clean() -> None:
    """config/*.toml and group_vars/all.yml share no keys in this project."""
    errors = validate()
    assert errors == []


def test_validate_no_duplicates_detects_overlap() -> None:
    """Overlapping keys between TOML and YAML are reported."""
    from unittest.mock import patch

    import src.utils.validate_no_duplicates as vnd

    toml_keys = {"env", "shared_key"}
    yaml_keys = {"project_name", "shared_key"}

    with (
        patch.object(vnd, "load_toml_keys", return_value=toml_keys),
        patch.object(vnd, "load_yaml_keys", return_value=yaml_keys),
    ):
        errors = vnd.validate()

    assert len(errors) == 1
    assert "shared_key" in errors[0]
