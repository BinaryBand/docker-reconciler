import sys
import tomllib
from pathlib import Path
from typing import Any, cast

import yaml

CONFIG_DIR = Path("config")
GROUP_VARS = Path("ansible/group_vars/all.yml")


def load_toml_keys() -> set[str]:
    keys: set[str] = set()
    for path in CONFIG_DIR.glob("*.toml"):
        with path.open("rb") as f:
            data: Any = tomllib.load(f)
            if isinstance(data, dict):
                keys.update(cast(dict[str, Any], data).keys())
    return keys


def load_yaml_keys() -> set[str]:
    with GROUP_VARS.open() as f:
        data: Any = yaml.safe_load(f) or {}
    if isinstance(data, dict):
        return set(cast(dict[str, Any], data).keys())
    return set()


def validate() -> list[str]:
    overlap = load_toml_keys() & load_yaml_keys()
    return [
        f"ERROR: key '{k}' declared in both config/*.toml and group_vars/all.yml"
        for k in sorted(overlap)
    ]


if __name__ == "__main__":
    errors = validate()
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
