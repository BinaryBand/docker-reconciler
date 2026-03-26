
# Docker Reconciler Project

A reference implementation of a reconciliation loop for Docker services, built following the playbook architecture.

## Getting Started

1. **Install pre-commit hooks**:
   ```bash
   pre-commit install --hook-type pre-push
   ```

2. **Run the reconciler**:
   ```bash
   python -m src.main
   ```

## Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [MODELS.md](MODELS.md)
- [CONTRIBUTING.md](CONTRIBUTING.md)

See `../project-playbook/docker-reconciler-plan.md` for full design details.
# docker-reconciler
