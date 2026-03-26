# Contributing

## Setup

Open the project in VS Code and select **Reopen in Container** when prompted (requires the
[Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
extension). The container builds automatically:

- Python 3.11 on Debian
- All dev dependencies installed via `pip install -e '.[dev]'`
- Pre-commit hooks wired up (`--hook-type pre-push`)

No manual tool installation required.

## Validation Workflow

```bash
pyright src/                                        # type check
ruff check src/ && ruff format src/ --check        # lint + format
lizard src/ -C 5 -L 25 -a 4                        # complexity gates
lint-imports                                        # import boundaries
pytest -v                                           # tests
python -m src.main                                  # smoke test
```

Pre-commit runs steps 1–4 automatically on every push.

## PR Checklist

- [ ] All automated checks pass
- [ ] No vars, secrets, or paths declared outside Ansible
- [ ] No Ansible queries mid-reconciliation
- [ ] No CQS violations — functions either mutate or return, not both
- [ ] Tests added or updated
- [ ] `ARCHITECTURE.md` updated if any structural decision changed
