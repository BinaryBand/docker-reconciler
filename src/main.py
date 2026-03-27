"""Main entry point for the docker-reconciler application."""

import sys

from src.models.manifest import ServiceManifest
from src.models.state import StateLabel, TransitionMap
from src.reconciler.controller import reconcile
from src.reconciler.model import ReconcilerConfig
from src.utils.ansible import load_inventory, load_manifests
from src.utils.config import load_config
from src.utils.executor import run_command
from src.utils.log import setup_logging
from src.utils.validate_contract import validate_contract
from src.utils.validate_manifest import validate_manifest


def _validate_inputs(manifests: list[ServiceManifest]) -> bool:
    print("Validating manifests...")
    result = validate_manifest(manifests)
    if not result.valid:
        print(f"Validation failed: {result.errors}")
        return False
    contract = validate_contract(manifests, "docker-compose.yml")
    if not contract.valid:
        print(f"Contract validation failed: {contract.errors}")
        return False
    return True


def main() -> None:
    """Execute the main reconciliation loop."""
    config = load_config("dev")
    manifests = load_manifests("ansible/manifests")
    if not _validate_inputs(manifests):
        sys.exit(1)
    setup_logging(config.log_level)
    load_inventory("ansible/inventory/hosts")
    recon_config = ReconcilerConfig(
        desired_state=StateLabel.T5,
        transition_map=TransitionMap(),
        max_retries=config.reconciler_max_retries,
        dry_run=False,
    )
    reconcile(StateLabel.T5, recon_config, manifests, run_command)
    print("Reconciliation complete.")


if __name__ == "__main__":
    main()
