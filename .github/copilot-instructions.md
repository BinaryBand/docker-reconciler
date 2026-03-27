# Copilot Instructions

## Project Overview

`docker-reconciler` is a reconciliation-loop state machine that manages three Docker services (Baikal, Jellyfin, Restic) through a T0→T5 lifecycle. Python orchestrates; Ansible provisions storage and secrets; Docker Compose runs services; TOML holds runtime config.

## Tech Stack

| Concern | Tool |
| --- | --- |
| Language | Python 3.11+ |
| Data validation | Pydantic v2 |
| Provisioning | Ansible |
| Container runtime | Docker Compose |
| Runtime config | TOML (`tomllib`) |
| Linting / formatting | Ruff |
| Type checking | Pyright (strict) |
| Complexity gate | Lizard |
| Import boundaries | import-linter |
| Tests | pytest |

## Development Setup

```bash
poetry install
pre-commit install --hook-type pre-push
```

Development target: WSL with base Debian compatibility. Use `brew install` instead of root installations for any new tools.

## Quality Gates

All gates run automatically on `git push` via pre-commit hooks. Run them manually before pushing:

```bash
pytest                                               # unit tests
ruff check src/ && ruff format src/ --check          # lint + format
pyright src/                                         # strict type checking
lizard src/ -C 5 -L 25 -a 4                          # complexity limits
lint-imports                                         # import boundary enforcement
python -m src.utils.validate_contract                # UIDs/paths match manifests
python -m src.utils.validate_no_duplicates           # no value declared twice
```

**Complexity limits (Lizard):**
- Cyclomatic complexity ≤ 5
- Function length ≤ 25 lines
- Parameters per function ≤ 4

## Architecture Rules

All rules are enforced mechanically — treat a failing gate as a build error.

### Unidirectional Data Flow

All contracts route through Python (Orchestration). No concern communicates with another directly.

```
main.py  →  models/*
main.py  →  reconciler/*
main.py  →  utils/*
reconciler/*  →  models/* only
utils/*       →  models/* only
models/*      →  nothing
```

### The Pydantic Rule

Every value crossing a module boundary must be a Pydantic model or typed primitive.

**Banned:** `dict`, `list` without type parameters, `Any`, `object`, untyped return values.

**Required:** Pydantic model or `str`, `int`, `float`, `bool`, `list[T]`, `tuple[T, ...]`.

Raw parsed data (YAML blobs, JSON dicts, subprocess output) must be coerced to Pydantic models at the ingestion point and never passed further.

### T0 Gate

All manifests must pass Pydantic validation before any command is issued. A malformed manifest halts the orchestrator immediately — no provisioning, no service start.

### Startup Sequence

```
T0: Python validates all manifests
T1: Ansible provisions volumes
T2: Ansible applies permissions and ACLs
T3: Docker Compose starts services
T4: Post-start hooks run
T5: Health checks pass
```

### Secrets

Secrets live in Ansible Vault only. Never in manifests, TOML config, or Compose files. Never query Ansible mid-reconciliation.

### Module Responsibilities

- **`models/`** — pure Pydantic shapes; no I/O; no imports from elsewhere in `src/`
- **`reconciler/controller.py`** — compares desired vs actual `SystemState`; returns typed commands; never reads files or spawns subprocesses
- **`reconciler/observer.py`** — the only reconciler module that touches external state
- **`reconciler/transitions.py`** — pure logic; no I/O
- **`utils/`** — raw data ingestion and coercion; all subprocess output coerced to Pydantic models here
- **`main.py`** — entry point only; no business logic; no raw data types

## Coding Style

- **Entry points** defined in `pyproject.toml` `[project.scripts]`; invoked as `python -m module`
- **All executable scripts must be Python** — no shell scripts
- **Early returns** over nested conditionals
- **Functions do one thing**: if a function needs more than 25 lines, split it
- **CQS**: functions either mutate state or return a value, not both
- **No mutable globals**
- **No silent exception swallowing**
- Line length: 88 characters; indent: 4 spaces for Python, 2 for YAML/TOML/JSON

## Adding a New Service

1. Add `ansible/manifests/<service>.yml` — declare UID, user, volumes, `read_access`
2. Add service to `docker-compose.yml` — images, healthchecks, runtime config only
3. `validate_contract` will assert UIDs and paths match
4. Ansible `roles/storage/` provisions from the manifest automatically

## Contribution Workflow

```
1. Branch from main
2. Make changes
3. pytest && ruff check src/ && pyright src/ && lizard src/ -C 5 -L 25 -a 4
4. Push — pre-commit hooks run automatically
5. Open PR
```

### PR Checklist

- [ ] All automated checks pass (`ruff`, `pyright`, `lizard`, `lint-imports`, `validate_contract`, `validate_no_duplicates`, `pytest`)
- [ ] No vars, secrets, or paths declared outside Ansible
- [ ] No Ansible queries mid-reconciliation
- [ ] No CQS violations
- [ ] Tests added or updated
- [ ] `ARCHITECTURE.md` updated if any structural decision changed
