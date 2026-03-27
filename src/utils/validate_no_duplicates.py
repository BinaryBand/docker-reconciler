import sys
import tomllib
from pathlib import Path

import yaml

CONFIG_DIR = Path("config")
GROUP_VARS = Path("ansible/group_vars/all.yml")


def load_toml_keys() -> set[str]:
    keys: set[str] = set()
    for path in CONFIG_DIR.glob("*.toml"):
        with path.open("rb") as f:
            keys.update(tomllib.load(f).keys())
    return keys


def load_yaml_keys() -> set[str]:
    with GROUP_VARS.open() as f:
        data = yaml.safe_load(f) or {}
    return set(data.keys())


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
