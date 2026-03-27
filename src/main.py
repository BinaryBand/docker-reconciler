from src.models.state import StateLabel
from src.reconciler.controller import reconcile
from src.reconciler.model import ReconcilerConfig
from src.utils.ansible import load_manifests
from src.utils.config import load_config


def main() -> None:
    # 1. Load config
    config = load_config("dev")

    # 2. Load manifests
    manifests = load_manifests("ansible/manifests")

    # 3. T0 gate (validate)
    print("Validating manifests...")
    from src.utils.validate_contract import validate_contract
    from src.utils.validate_manifest import validate_manifest

    result = validate_manifest(manifests)
    if not result.valid:
        print(f"Validation failed: {result.errors}")
        exit(1)
    contract = validate_contract(manifests, "docker-compose.yml")
    if not contract.valid:
        print(f"Contract validation failed: {contract.errors}")
        exit(1)

    # 4. Build ReconcilerConfig
    recon_config = ReconcilerConfig(
        desired_state=StateLabel.T5,
        max_retries=config.reconciler_max_retries,
        dry_run=False,
    )

    # 5. Reconcile
    reconcile(StateLabel.T5, recon_config, manifests)
    print("Reconciliation complete.")


if __name__ == "__main__":
    main()
