# Docker Reconciler

A reference implementation of a reconciliation loop for Docker services. Ansible provisions storage at T1/T2, Docker Compose starts services at T3, and a Python state machine drives the full T0→T5 lifecycle.

**Services managed:** Baikal (CalDAV/CardDAV), Jellyfin (media), Restic (on-demand backup).

---

## Setup

### Recommended: Dev Container

Open the project in VS Code and select **Reopen in Container** when prompted (requires the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension). The container automatically installs all dependencies and pre-commit hooks.

### Manual

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install --hook-type pre-push
```

Requires Python 3.11+, Docker, Docker Compose, and Ansible.

---

## Running tests

```bash
pytest -v
```

27 tests, all passing. See [TESTING.md](TESTING.md) for the full coverage plan.

---

## Quality checks

These run automatically on `git push` via pre-commit. Run manually at any time:

```bash
pyright src/                                     # strict type checking
ruff check src/ && ruff format src/ --check      # lint + format
lizard src/ -C 5 -L 25 -a 4                      # complexity gates
lint-imports                                     # import boundary enforcement
```

---

## Provisioning

Ansible creates and permissions all bind-mount directories before services start. This corresponds to reconciler states T1 (provision) and T2 (configure).

```bash
# Apply provisioning
ansible-playbook ansible/playbooks/provision.yml -i ansible/inventory/hosts

# Dry run — check what would change without applying
ansible-playbook ansible/playbooks/provision.yml -i ansible/inventory/hosts --check
```

Directories created:

| Path | Owner | Mode | Service |
|---|---|---|---|
| `/srv/baikal/config` | 1001 | 0750 | baikal |
| `/srv/baikal/data` | 1001 | 0750 | baikal |
| `/srv/jellyfin/config` | 1000 | 0750 | jellyfin |
| `/srv/jellyfin/cache` | 1000 | 0750 | jellyfin |
| `/srv/jellyfin/data` | 1000 | 0750 | jellyfin |
| `/srv/media` | 1000 | 0755 | jellyfin |
| `/srv/logs` | 1000 | 0750 | jellyfin |
| `/srv/restic/repo` | 1002 | 0700 | restic |
| `/srv/restic/backups` | 1002 | 0750 | restic |

---

## Starting services

Copy the example env file and set the required secret:

```bash
cp .env.example .env
# Edit .env and set RESTIC_PASSWORD
```

Start Baikal and Jellyfin (T3):

```bash
docker compose up -d
```

Run a Restic backup on demand:

```bash
docker compose --profile on-demand run restic backup /backups
```

View logs:

```bash
docker compose logs -f
```

Stop all services:

```bash
docker compose down
```

---

## Service endpoints

| Service | URL |
|---|---|
| Jellyfin | http://localhost:8096 |
| Baikal | http://localhost:5234 |

---

## Reconciliation walkthrough

The Python reconciler simulates the full T0→T5 state machine:

```bash
python -m src.main
```

| State | Meaning |
|---|---|
| T0 | Manifests validated (Pydantic) |
| T1 | Volumes provisioned (Ansible) |
| T2 | Permissions applied (Ansible) |
| T3 | Services started (Docker Compose) |
| T4 | Post-start hooks complete |
| T5 | Health checks pass — desired state reached |
| F1–F5 | Failure at the corresponding T-state — reconciler halts |

The observer is currently a simulation that steps through T0→T5 on each call. `load_manifests()` and `issue_command()` are stubs pending real implementation.

---

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — import boundaries and design constraints
- [MODELS.md](MODELS.md) — data model reference
- [CONTRIBUTING.md](CONTRIBUTING.md) — validation workflow and PR checklist
- [MIGRATION.md](MIGRATION.md) — how cloud-apps services were migrated in
- [TESTING.md](TESTING.md) — test coverage plan
