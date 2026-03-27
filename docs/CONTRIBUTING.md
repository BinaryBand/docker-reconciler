# Contributing

Bounded constraints for contributors. The goal is a solution space tight enough that any output passing these rules is consistent, reviewable, and mergeable without negotiation.

See `ARCHITECTURE.md` for tool responsibilities and structural decisions.

* * *

## Setup

WSL with base Debian compatibility is the development target.

```bash
sudo apt install python3 python3-venv python3-pip
pip install ansible ansible-lint molecule pyyaml lizard pre-commit import-linter pyright pydantic
```

Install pre-commit hooks once after cloning:

```bash
pre-commit install --hook-type pre-push
```

Open in VS Code from inside WSL:

```bash
code .
```

### Universal Config Files

All tooling behaviour is driven by committed config files — editor-agnostic, picked up automatically by any LSP-capable editor.

**`pyproject.toml`** — merge into existing project config:

```toml
[tool.ruff]
target-version = "py311"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "D"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.pyright]
pythonVersion = "3.11"
typeCheckingMode = "strict"
venvPath = "."
venv = ".venv"

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.importlinter]
root_package = src

[[tool.importlinter.contracts]]
name = "Business logic confined to reconciler and models"
type = "forbidden"
source_modules = ["src.utils", "src.main"]
forbidden_modules = ["src.reconciler", "src.models"]
```

**`.ansible-lint`:**

```yaml
profile: production
exclude_paths:
  - ansible/molecule.yml
warn_list:
  - experimental
skip_list: []
```

**`.editorconfig`:**

```ini
root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.py]
indent_style = space
indent_size = 4

[*.{yml,yaml,toml,json,j2}]
indent_style = space
indent_size = 2
```

**`.pre-commit-config.yaml`:**

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-lint
        name: Ruff lint
        entry: .venv/bin/ruff check src/
        language: system
        pass_filenames: false

      - id: ruff-format
        name: Ruff format
        entry: .venv/bin/ruff format --check src/
        language: system
        pass_filenames: false

      - id: pyright
        name: Pyright type-check
        entry: .venv/bin/pyright src/
        language: system
        pass_filenames: false

      - id: lizard
        name: Complexity check
        entry: .venv/bin/lizard src/ -C 5 -L 25 -a 4
        language: system
        pass_filenames: false

      - id: contract-validation
        name: Service contract validation
        entry: .venv/bin/python -m utils.validate_contract
        language: system
        pass_filenames: false

      - id: duplicate-values
        name: Duplicate value check
        entry: .venv/bin/python -m utils.validate_no_duplicates
        language: system
        pass_filenames: false

      - id: import-boundaries
        name: Import boundary enforcement
        entry: .venv/bin/lint-imports
        language: system
        pass_filenames: false
```

Molecule is excluded — infrastructure provisioning is too slow for a push hook. Run it manually before opening a PR.

### VS Code

| Extension | ID | Required |
| --- | --- | --- |
| Remote - WSL | `ms-vscode-remote.remote-wsl` | Yes |
| Python | `ms-python.python` | Yes |
| Pylance | `ms-python.vscode-pylance` | Optional |
| Ruff | `charliermarsh.ruff` | Optional |
| Ansible | `redhat.ansible` | Optional |
| Error Lens | `usernamehehe.errorlens` | Optional |
| Even Better TOML | `tamasfe.even-better-toml` | Optional |
| Jinja | `samuelcolvin.jinjahtml` | Optional |

```bash
code --install-extension ms-vscode-remote.remote-wsl \
     --install-extension ms-python.python \
     --install-extension ms-python.vscode-pylance \
     --install-extension charliermarsh.ruff \
     --install-extension redhat.ansible \
     --install-extension usernamehehe.errorlens \
     --install-extension tamasfe.even-better-toml \
     --install-extension samuelcolvin.jinjahtml
```

**`.vscode/settings.json`:**

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "strict",
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.shell.linux": "/bin/bash",
  "files.associations": { "*.j2": "jinja-yaml", "*.toml": "toml" },
  "editor.formatOnSave": true,
  "[python]": { "editor.defaultFormatter": "charliermarsh.ruff" }
}
```

**`.vscode/tasks.json`:**

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate: Service Contract",
      "type": "shell",
      "command": "${workspaceFolder}/.venv/bin/python -m utils.validate_contract",
      "group": "test",
      "presentation": { "reveal": "always", "panel": "shared", "clear": true },
      "problemMatcher": {
        "owner": "contract",
        "fileLocation": ["relative", "${workspaceFolder}"],
        "pattern": {
          "regexp": "^(ERROR|WARN)\\s+(.+):(\\d+):\\s+(.+)$",
          "severity": 1, "file": 2, "line": 3, "message": 4
        }
      },
      "runOptions": { "runOn": "folderOpen" }
    },
    {
      "label": "Test: Molecule",
      "type": "shell",
      "command": "${workspaceFolder}/.venv/bin/molecule test -c ansible/molecule.yml",
      "group": "test",
      "presentation": { "reveal": "always", "panel": "dedicated", "clear": true },
      "problemMatcher": []
    },
    {
      "label": "Check: Complexity",
      "type": "shell",
      "command": "${workspaceFolder}/.venv/bin/lizard src/ -C 5 -L 25 -a 4 --output-file /tmp/lizard_out.txt; cat /tmp/lizard_out.txt",
      "group": "test",
      "presentation": { "reveal": "always", "panel": "shared", "clear": true },
      "problemMatcher": {
        "owner": "lizard",
        "fileLocation": ["relative", "${workspaceFolder}"],
        "pattern": {
          "regexp": "^(.+):(\\d+):\\s+(.+)\\s+\\(complexity:\\s*(\\d+)\\)$",
          "file": 1, "line": 2, "message": 3
        }
      }
    }
  ]
}
```

**`.vscode/keybindings.json`:**

```json
[
  { "key": "ctrl+shift+v", "command": "workbench.action.tasks.runTask", "args": "Validate: Service Contract" },
  { "key": "ctrl+shift+m", "command": "workbench.action.tasks.runTask", "args": "Test: Molecule" },
  { "key": "ctrl+shift+z", "command": "workbench.action.tasks.runTask", "args": "Check: Complexity" }
]
```

Snippets — commit `.vscode/snippets/` to the repository. See existing snippet files for Ansible, TOML, Jinja2, and Python patterns.

* * *

## Rules

Every rule is paired with its enforcement tier. Rules marked **review** have no automated mechanism — they are candidates for future tooling.

| Rule | Tier | Mechanism |
| --- | --- | --- |
| Function length ≤ 25 lines | Automated | Ruff |
| Cyclomatic complexity ≤ 5 | Automated | Lizard |
| Nesting depth ≤ 3 | Automated | Ruff |
| Parameters per function ≤ 4 | Automated | Ruff |
| No type errors | Automated | Pyright (`strict`) |
| No lint violations | Automated | Ruff |
| All public functions have docstrings | Automated | Ruff (`D`) |
| No mutable globals | Automated | Pyright (`strict`) |
| No silent exception swallowing | Automated | Ruff (`B001`, `S110`) |
| No shell scripts — Python only | Automated | Ruff + pre-commit |
| Service contract consistent | Automated | `validate_contract.py` — pre-push hook + VS Code task |
| No value declared in two places | Automated | `validate_no_duplicates.py` — pre-push hook |
| No business logic outside `src/reconciler/` and `src/models/` | Automated | `import-linter` — pre-push hook |
| No vars, secrets, or paths outside Ansible | Review | — |
| No Ansible queries mid-reconciliation | Review | — |
| No CQS violations — functions either mutate or return, not both | Review | — |

Prefer early returns over nested conditionals. If a function needs more than 25 lines, it has more than one responsibility — split it.

**Review-only rules** are enforced by the PR checklist. Each is a candidate for automation.

* * *

## Validation Scripts

### `src/utils/validate_contract.py`

Validates `docker-compose.yml` against `ansible/manifests/`. Called by the pre-push hook and VS Code task.

```python
"""
Validates docker-compose.yml against ansible/manifests/*.yml.
Format: SEVERITY file:line message — exit 1 on errors, 0 if clean.
"""
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

from models.manifest import ServiceManifest

MANIFESTS_DIR = Path("ansible/manifests")
COMPOSE = Path("docker-compose.yml")


def load_manifests() -> list[ServiceManifest]:
    """Load and validate all service manifests."""
    manifests = []
    for path in MANIFESTS_DIR.glob("*.yml"):
        with path.open() as f:
            manifests.append(ServiceManifest(**yaml.safe_load(f)))
    return manifests


def load_compose() -> dict:
    """Load docker-compose.yml service definitions."""
    with COMPOSE.open() as f:
        return yaml.safe_load(f).get("services", {})


def validate() -> list[str]:
    """Assert Compose UIDs and volume paths match manifests."""
    errors: list[str] = []
    try:
        manifests = load_manifests()
    except ValidationError as e:
        return [f"ERROR {MANIFESTS_DIR}:1: invalid manifest — {e}"]

    compose = load_compose()
    for svc in manifests:
        if svc.service not in compose:
            errors.append(f"ERROR {COMPOSE}:1: service '{svc.service}' missing from Compose")
            continue
        c = compose[svc.service]
        if str(c.get("user")) != str(svc.uid):
            errors.append(
                f"ERROR {COMPOSE}:1: service '{svc.service}' UID mismatch "
                f"(expected {svc.uid}, got {c.get('user')})"
            )
        declared_mounts = [v.split(":")[0] for v in c.get("volumes", [])]
        for vol in svc.volumes:
            if vol.path not in declared_mounts:
                errors.append(
                    f"ERROR {COMPOSE}:1: service '{svc.service}' "
                    f"volume '{vol.path}' not mounted in Compose"
                )
    return errors


if __name__ == "__main__":
    errors = validate()
    for e in errors:
        print(e)
    sys.exit(1 if errors else 0)
```

### `src/utils/validate_no_duplicates.py`

Detects keys declared in both `config/*.toml` and `ansible/group_vars/all.yml`.

```python
"""
Detects values declared in both config/*.toml and ansible/group_vars/all.yml.
Exit 1 if overlapping keys found, 0 if clean.
"""
import sys
from pathlib import Path

import tomllib
import yaml

CONFIG_DIR = Path("config")
GROUP_VARS = Path("ansible/group_vars/all.yml")


def load_toml_keys() -> set[str]:
    """Collect all top-level keys from every TOML config file."""
    keys: set[str] = set()
    for path in CONFIG_DIR.glob("*.toml"):
        with path.open("rb") as f:
            keys.update(tomllib.load(f).keys())
    return keys


def load_yaml_keys() -> set[str]:
    """Collect all top-level keys from group_vars/all.yml."""
    with GROUP_VARS.open() as f:
        data = yaml.safe_load(f) or {}
    return set(data.keys())


def validate() -> list[str]:
    """Assert no key appears in both TOML config and Ansible vars."""
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
```

* * *

## Contribution Workflow

```
0. After cloning:              pre-commit install --hook-type pre-push
1. Branch from main
2. Run contract validation:    python -m utils.validate_contract
3. Run duplicate check:        python -m utils.validate_no_duplicates
4. Run import boundaries:      lint-imports
5. Run complexity check:       lizard src/ -C 5 -L 25 -a 4
6. Run linter:                 ruff check src/ && ruff format src/
7. Run type-check:             pyright src/
8. Run tests:                  pytest
9. Run molecule (Ansible):     molecule test -c ansible/molecule.yml
10. Push — pre-commit hooks run steps 2–7 automatically
11. Open PR — checklist below
```

### PR Checklist

- [ ] All automated checks pass
- [ ] No vars, secrets, or paths declared outside Ansible
- [ ] No Ansible queries mid-reconciliation
- [ ] No CQS violations — functions either mutate or return, not both
- [ ] Tests added or updated
- [ ] `ARCHITECTURE.md` updated if any structural decision changed
