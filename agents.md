# AGENTS.md

## Setup

```bash
poetry install
pre-commit install --hook-type pre-push
```

- Use `brew install` instead of root installations.
- Development target: WSL with base Debian compatibility.

## Quality Gates (must pass before every push)

```bash
pytest                          # unit tests
ruff check src/ && ruff format src/ --check
pyright src/
lizard src/ -C 5 -L 25 -a 4
lint-imports
python -m src.utils.validate_contract
python -m src.utils.validate_no_duplicates
```

## Key Rules

- Every value crossing a module boundary must be a Pydantic model or typed primitive — no `dict`, `Any`, or untyped structures.
- Import boundaries are enforced by `import-linter`: `models/` imports nothing; `reconciler/` and `utils/` import from `models/` only.
- All executable scripts must be Python; no shell scripts.
- Functions: ≤ 25 lines, cyclomatic complexity ≤ 5, ≤ 4 parameters.
- Secrets live in Ansible Vault only — never in TOML, manifests, or Compose files.
- CQS: functions either mutate state or return a value, not both.

See `.github/copilot-instructions.md` for full architecture and contribution details.
