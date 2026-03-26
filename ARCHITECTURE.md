# Architecture

See `../project-playbook/ARCHITECTURE.md` for the full design reference.

## Development Environment

Develop inside the provided dev container (`.devcontainer/devcontainer.json`). The container
image is `mcr.microsoft.com/devcontainers/python:3.11` (Debian-based), matching the base
Debian compatibility target. Open the project in VS Code and select **Reopen in Container**.

## Concerns & Tools

| Concern | Tool |
|---------|------|
| State & Secrets | Ansible |
| Orchestration | Python + Pydantic |
| Service Topology | Docker Compose |
| Config | TOML |

## Import Boundaries

```text
main.py        → models/*, reconciler/*, utils/*
reconciler/*   → models/* only
utils/*        → models/* only
models/*       → nothing
```

Enforced by `import-linter` on every push.

## Startup Sequence

```text
T0  Python validates all manifests (Pydantic — no command issued until clean)
T1  Ansible provisions volumes
T2  Ansible applies permissions and ACLs
T3  Docker Compose starts services
T4  Post-start hooks run
T5  Health checks pass — desired state reached
```

F1–F5 are the corresponding failure states. The reconciler halts and reports on any F-state.
