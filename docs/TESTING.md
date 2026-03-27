# Testing Plan

Project-specific testing plan for `docker-reconciler`. Read `PLAYBOOK.md` Step 5 for the abstract guidelines this document is derived from.

See `ARCHITECTURE.md` for module ownership, import boundaries, and startup sequencing.

* * *

## Quick Reference

```bash
# All unit tests — no external dependencies required
pytest

# Single module
pytest tests/test_models.py
pytest tests/test_reconciler.py
pytest tests/test_utils.py

# Quality gates (run before every push)
python3 runbook/.quality.py

# Compose↔manifest contract check
python -m src.utils.validate_contract

# Config/group_vars overlap check
python -m src.utils.validate_no_duplicates
```

* * *

## Test Tiers

| Tier | Location | Trigger | External deps |
| --- | --- | --- | --- |
| Unit | `tests/` | Every commit | None |
| Integration | `tests/` (marked) | Pre-push hook | Filesystem only |
| End-to-end | Molecule / manual | Opt-in | Docker, Ansible, host |

All tests in `tests/` are unit tests unless the test name or a marker explicitly says otherwise. Any test that touches the real filesystem, Docker socket, or network must be labelled and excluded from the default run.

* * *

## Unit Tests by Module

### `models/manifest.py` — `VolumeSpec`, `ServiceManifest`

| Test | Description |
| --- | --- |
| `test_volume_spec_mode` | Valid octal mode string accepted |
| `test_volume_spec_invalid_chars` | Non-octal characters in mode rejected |
| `test_volume_spec_mode_no_leading_zero` | Mode without leading `0` rejected |
| `test_service_manifest_creation` | All fields round-trip correctly |
| `test_service_manifest_no_self_read_access` | `read_access` containing the service's own user raises `ValueError` |

### `models/state.py` — `StateLabel`, `SystemState`, `TransitionMap`

| Test | Description |
| --- | --- |
| `test_state_label` | `StateLabel.T0` equals string `"T0"` |
| `test_failure_state_labels` | All F-states start with `"F"` |
| `test_system_state_t0_all_false` | All boolean fields false at T0 |
| `test_system_state_t5_all_true` | All boolean fields true at T5 |
| `test_system_state_t3_partial` | `volumes` and `compose` true; `post_start` and `health` false at T3 |
| `test_transition_map` | Basic forward step: T0 → T1 |
| `test_is_legal_transition_valid` | All documented forward transitions are legal |
| `test_is_legal_transition_invalid` | Skipping a step, wrong F-state recovery, and reverse steps are illegal |
| `test_next_toward_each_step` | Each T-state step advances correctly toward T5 |
| `test_next_toward_direct_reach` | Returns desired when it is a direct legal transition |
| `test_next_toward_no_forward_path` | Returns `None` when no forward path exists (e.g. T5 → T3) |
| `test_next_toward_f_state_to_t0` | All F-states can reach T0 |
| `test_next_toward_f_state_no_forward_to_t5` | F-states return `None` when desired is T5 |
| `test_next_toward_deterministic` | Repeated calls with the same inputs return the same result |

### `models/service.py` — `ClusterState`, `ContainerState`

| Test | Description |
| --- | --- |
| `test_cluster_state` | Single running, healthy container: `all_running` and `all_healthy` both true |
| `test_cluster_state_mixed_running` | One running, one stopped: neither `all_running` nor `all_healthy` |
| `test_cluster_state_empty` | Empty container list: `all()` vacuously true — documented behaviour |

### `reconciler/controller.py`

| Test | Description |
| --- | --- |
| `test_reconcile_loop_terminates` | Returns immediately when observer already reports desired state |
| `test_reconcile_halts_on_failure_state` | `FailureStateError` raised when observer reports any F-state |
| `test_all_failure_states_raise_failure_state_error` | Parametrised across F1–F5 |
| `test_reconcile_exhausts_retries` | `RuntimeError` raised when max retries exceeded |
| `test_reconcile_no_transition_path` | `IllegalTransitionError` raised when no legal path exists |
| `test_reconcile_dry_run_skips_commands` | `run_command` callable is never called when `dry_run=True` |
| `test_reconcile_runner_called_on_advance` | `run_command` is called once per advancement step with the correct target state |
| `test_failure_state_error_is_runtime_error` | Exception hierarchy: `FailureStateError` is a `RuntimeError` |
| `test_illegal_transition_error_is_value_error` | Exception hierarchy: `IllegalTransitionError` is a `ValueError` |

### `reconciler/observer.py`

Observer tests use `patch` to isolate filesystem and Docker checks. No real volumes, permissions, or containers are created.

| Test | Description |
| --- | --- |
| `test_observer_t0_when_volumes_missing` | `_check_volumes` returns `False` → label is T0 |
| `test_observer_t1_when_permissions_wrong` | Volumes present, `_check_permissions` returns `False` → label is T1 |
| `test_observer_t2_when_compose_not_running` | Volumes and permissions OK, no running containers → label is T2 |
| `test_observer_t3_when_partially_running` | Some containers running, not all → label is T3 |
| `test_observer_t4_when_health_check_failing` | All running, at least one `healthy=False` → label is T4 |
| `test_observer_t5_when_all_healthy` | All running and all `healthy=True` → label is T5 |
| `test_observer_t5_when_no_healthcheck` | All running, `healthy=None` (no healthcheck defined) → treated as healthy → T5 |

### `reconciler/transitions.py`

| Test | Description |
| --- | --- |
| `test_transition_map_all_t_states` | T0→T1 through T4→T5 each have the correct first forward step |
| `test_transition_map_f_states_recover_to_t0` | Every F-state maps only to T0 |

### `utils/executor.py`

| Test | Description |
| --- | --- |
| `test_executor_run_command_calls_subprocess_for_known_state` | T1 maps to `ansible-playbook --tags volumes`; `subprocess.run` called once with correct args |
| `test_executor_run_command_noop_for_unmapped_state` | T0, T4, and T5 have no mapped command; `subprocess.run` is not called |

### `utils/validate_manifest.py`

| Test | Description |
| --- | --- |
| `test_validate_manifest_empty_list` | Empty manifest list passes validation |
| `test_validate_manifest_single_service` | Single valid manifest passes |
| `test_validate_manifest_duplicates` | Two manifests with the same UID: `valid=False`, error on `uid` field |
| `test_validate_manifest_volume_path_duplicate` | Two manifests sharing a volume path: `valid=False`, error on `volumes` field |
| `test_validate_manifest_all_unique` | Three distinct manifests (baikal, jellyfin, restic) pass the T0 gate |

### `utils/validate_contract.py`

| Test | Description |
| --- | --- |
| `test_validate_contract_service_missing_from_compose` | Manifest service absent from Compose: `valid=False`, error on `service` field |
| `test_validate_contract_uid_mismatch` | Compose `user` field does not match manifest UID: error on `uid` field |
| `test_validate_contract_volume_missing_from_compose` | Manifest volume path not mounted in Compose: error on `volumes` field |
| `test_validate_contract_passes_with_real_compose` | All three project manifests validate cleanly against `docker-compose.yml` |

### `utils/validate_no_duplicates.py`

| Test | Description |
| --- | --- |
| `test_validate_no_duplicates_clean` | Current project config and group_vars share no keys |
| `test_validate_no_duplicates_detects_overlap` | Patched key sets with a shared key: overlap reported correctly |

### `utils/config.py`

| Test | Description |
| --- | --- |
| `test_load_config_dev` | `config/dev.toml` loads and deserialises to `AppConfig` correctly |
| `test_load_config_missing_file` | Non-existent env name raises `FileNotFoundError` |

* * *

## Integration Tests

Integration tests interact with real system state. They are slower and require more setup. Mark them with `@pytest.mark.integration` and exclude from the default `pytest` run via:

```toml
# pyproject.toml
[tool.pytest.ini_options]
addopts = "-m 'not integration'"
markers = ["integration: requires filesystem or Docker"]
```

### Planned Integration Tests

| Test | Description | Requires |
| --- | --- | --- |
| `test_observer_real_volumes` | Create real tmp directories matching a manifest; verify observer returns T1 or T2 | Filesystem write access |
| `test_executor_dry_subprocess` | Run executor against a no-op script; confirm subprocess exit codes propagate | Filesystem, Python |
| `test_validate_contract_against_live_compose` | Same as unit test but run against the project's real compose file on disk | None (already covered) |

* * *

## End-to-End Tests

End-to-end tests require Docker and Ansible. They are opt-in and run in a dedicated environment (local VM or CI matrix job).

### Molecule Scenarios

Declared in `ansible/molecule.yml` (to be added). Standard scenarios:

| Scenario | Description |
| --- | --- |
| `default` | Converge from T0 to T5: provision volumes, set permissions, start services, health checks pass |
| `idempotency` | Run converge twice; assert no changes on second run |
| `failure-recovery` | Inject a permission failure at T2; verify system reaches F2 and halts |

### Reconciler Dry-Run Smoke Test

```bash
python -m src.main --dry-run
```

With `dry_run=True` in `ReconcilerConfig`, the reconciler must complete all observation steps without issuing any subprocess commands. Verify by examining logs for no `ansible-playbook` or `docker compose` invocations.

* * *

## T0 Gate Coverage

The T0 gate is the most critical boundary in the project. It must be fully covered.

| Scenario | Expected result |
| --- | --- |
| Valid manifests, valid compose | Reconciler advances to T1 |
| Duplicate UID across manifests | `validate_manifest` returns `valid=False`; reconciler halts at T0 |
| Duplicate volume path across manifests | `validate_manifest` returns `valid=False`; reconciler halts at T0 |
| Service in manifest absent from compose | `validate_contract` returns `valid=False`; reconciler halts at T0 |
| UID mismatch between manifest and compose | `validate_contract` returns `valid=False`; reconciler halts at T0 |
| Volume in manifest not mounted in compose | `validate_contract` returns `valid=False`; reconciler halts at T0 |
| Malformed YAML in manifest | `load_manifests` raises before T0 gate runs |
| `config/{env}.toml` missing | `load_config` raises `FileNotFoundError` before T0 gate runs |

* * *

## Import Boundary Tests

Import boundaries are enforced by `import-linter` on every push. Violations are build failures.

The contracts declared in `pyproject.toml`:

- `src.reconciler` must not import `src.utils`
- `src.utils` must not import `src.reconciler`
- `src.models` must not import `src.reconciler` or `src.utils`

These are tested automatically by the `import-linter` pre-push hook. No additional pytest coverage is required — the gate is the test.

* * *

## Regression Checklist

When adding a new service manifest:

- [ ] `validate_manifest` passes with the new manifest included
- [ ] `validate_contract` passes against `docker-compose.yml`
- [ ] `test_validate_contract_passes_with_real_compose` still passes
- [ ] `test_validate_no_duplicates_clean` still passes (no key overlap with group_vars)
- [ ] Observer tests still pass (new service does not affect derived state labels)

When modifying the transition map:

- [ ] `test_is_legal_transition_valid` and `test_is_legal_transition_invalid` updated
- [ ] `test_next_toward_each_step` updated if forward steps change
- [ ] `test_transition_map_all_t_states` and `test_transition_map_f_states_recover_to_t0` updated

When adding a new reconciliation step (new T-state):

- [ ] New `StateLabel` added to `models/state.py`
- [ ] `TransitionMap` updated with the new legal transitions
- [ ] `SystemState.from_label` updated with the new boolean flag
- [ ] `_COMMANDS` in `utils/executor.py` updated with the subprocess command for the new step
- [ ] Observer derives the new label under the correct infrastructure conditions
- [ ] All existing transition and observer tests updated
