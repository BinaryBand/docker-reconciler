# Deviations: docs/ vs. Implementation

Comparison of `docs/ARCHITECTURE.md`, `docs/MODELS.md`, `docs/CONTRIBUTING.md`, and `docs/PLAYBOOK.md` against the current codebase. Each deviation notes which source has the better practice and what should change.

---

## Summary table

| # | Location | Deviation | Best from | Action |
|---|---|---|---|---|
| 1 | `src/models/manifest.py` | `read_access` validates against `service` name, not `user` name | docs | Fix validator |
| 2 | `src/models/service.py` | `healthy` and `exit_code` are required, not optional | docs | Make optional |
| 3 | `src/models/state.py` | `SystemState` uses `dict[str, bool]`; docs use flat typed fields | docs + current | Flat fields, keep `from_label()` |
| 4 | `src/models/state.py` | `TransitionMap` is a plain class with single-target dict; docs use Pydantic with multi-path + F-state recovery | docs | Upgrade to Pydantic, multi-path |
| 5 | `src/reconciler/controller.py` | Uses `transition_map.get()` on raw dict instead of `TransitionMap.next_toward()` | docs | Use `next_toward()` |
| 6 | `src/utils/ansible.py` | `load_manifests()` is a stub; `AnsibleInventory` is under-typed | docs | Implement YAML loading; add `AnsibleHost` |
| 7 | `src/utils/validate_contract.py` | Stub — always returns valid | docs | Implement UID + volume path checks |
| 8 | `src/utils/validate_no_duplicates.py` | File does not exist | docs | Create — detect config/group_vars overlap |
| 9 | `src/main.py` | `validate_contract()` never called — T0 gate incomplete | docs | Call at T0 after `validate_manifest()` |
| 10 | `src/models/contract.py` | `ValidationResult.errors` is `List[ContractViolation]` | **current** | Keep — richer than docs' `list[str]` |
| 11 | `src/utils/config.py` | `AppConfig` has richer fields than docs' minimal spec | **current** | Keep — correct for this project |
| 12 | `pyproject.toml` | No `[tool.ruff.lint]` rules; no `import-linter` contracts | docs | Add lint rules; add correct contracts |
| 13 | `.editorconfig` | File missing | docs | Create |
| 14 | `.vscode/settings.json` | File missing | docs | Create |
| 15 | `.vscode/tasks.json` | File missing | docs | Create |
| 16 | `.pre-commit-config.yaml` | Missing `contract-validation` and `duplicate-values` hooks | docs | Add hooks |

---

## Deviation details

### 1 — `read_access` validator checks `service`, should check `user`

**Current** ([src/models/manifest.py](src/models/manifest.py)):
```python
if "service" in info.data and info.data["service"] in v:
```

**Docs** (`docs/MODELS.md`): validates against `user` (e.g. `"svc_baikal"`), not the service name (`"baikal"`). `read_access` lists usernames — granting `svc_worker` read access, not `worker`.

**Fix:** change the validator condition to check `info.data.get("user")`.

---

### 2 — `ContainerState` optional fields

**Current** ([src/models/service.py](src/models/service.py)):
```python
healthy: bool
exit_code: int
```

**Docs** (`docs/MODELS.md`): `healthy: bool | None = None`, `exit_code: int | None = None`. Health checks may not be configured and exit codes are not always available.

**Fix:** make both fields optional with `None` default. Update `all_healthy()` to check `c.healthy is True` (as docs specify).

---

### 3 — `SystemState` flat typed fields vs. dict

**Current** ([src/models/state.py](src/models/state.py)):
```python
class SystemState(BaseModel):
    label: StateLabel
    steps: dict[str, bool]
```

**Docs** (`docs/MODELS.md`):
```python
class SystemState(BaseModel):
    label: StateLabel
    volumes: bool = False
    permissions: bool = False
    compose: bool = False
    post_start: bool = False
    health: bool = False
```

Flat Pydantic fields are type-safe and self-documenting. The current `from_label()` factory is a **current-project improvement** not in docs — keep it.

**Field name mapping (current → docs):**
- `provisioned` → `volumes`
- `configured` → `permissions`
- `started` → `compose`
- `hooked` → `post_start`
- `healthy` → `health`

**Fix:** replace `steps: dict[str, bool]` with five flat fields; update `from_label()` to set them directly. Update `observer.py` and relevant tests.

---

### 4 — `TransitionMap`: plain class vs. Pydantic with multi-path transitions

**Current** ([src/models/state.py](src/models/state.py)):
```python
class TransitionMap:
    def __init__(self):
        self._transitions: dict[StateLabel, StateLabel] = {
            StateLabel.T0: StateLabel.T1, ...
        }
```
One target per state, no F-state recovery, no T0 reset path.

**Docs** (`docs/MODELS.md`):
```python
class TransitionMap(BaseModel):
    transitions: dict[StateLabel, list[StateLabel]] = {
        StateLabel.T0: [StateLabel.T1],
        StateLabel.T1: [StateLabel.T2, StateLabel.F1, StateLabel.T0],
        StateLabel.T2: [StateLabel.T3, StateLabel.F2, StateLabel.T0],
        StateLabel.T3: [StateLabel.T4, StateLabel.F3, StateLabel.T0],
        StateLabel.T4: [StateLabel.T5, StateLabel.F4, StateLabel.T0],
        StateLabel.T5: [StateLabel.T0],
        StateLabel.F1: [StateLabel.T0],
        ...
    }
    def next_toward(self, current, desired) -> StateLabel | None: ...
```
F-states and T5 can return to T0. Richer recovery model.

**Fix:** make `TransitionMap` a `BaseModel`, switch to `dict[StateLabel, list[StateLabel]]`, update `next_toward()` to select the best forward step from the legal list.

---

### 5 — `controller.py` uses raw dict `.get()` instead of `TransitionMap.next_toward()`

**Current** ([src/reconciler/controller.py](src/reconciler/controller.py)):
```python
transition_map = build_transition_map()   # returns dict
next_state = transition_map.get(current.label)
```

**Docs** architecture: `controller.py` should call `TransitionMap.next_toward()`. `build_transition_map()` in `transitions.py` should return a `TransitionMap` instance, not a raw dict.

**Fix:** update `transitions.py` to return `TransitionMap()`; update `controller.py` to call `transition_map.next_toward(current.label, desired)`.

---

### 6 — `load_manifests()` stub + thin `AnsibleInventory`

**Current** ([src/utils/ansible.py](src/utils/ansible.py)):
```python
def load_manifests(dir: str) -> list[ServiceManifest]:
    return []   # stub

class AnsibleInventory(BaseModel):
    hosts: dict[str, str]
```

**Docs** (`docs/CONTRIBUTING.md` + `docs/MODELS.md`): full YAML glob loading; typed `AnsibleHost` model.

**Fix — `load_manifests()`:**
```python
def load_manifests(dir: str) -> list[ServiceManifest]:
    manifests = []
    for path in Path(dir).glob("*.yml"):
        with path.open() as f:
            data = yaml.safe_load(f)
            if isinstance(data, list):
                manifests.extend(ServiceManifest(**item) for item in data)
            else:
                manifests.append(ServiceManifest(**data))
    return manifests
```

**Fix — `AnsibleInventory`:**
```python
class AnsibleHost(BaseModel):
    ansible_host: str
    ansible_user: str | None = None

class AnsibleInventory(BaseModel):
    hosts: dict[str, AnsibleHost] = {}
    vars: dict[str, str] = {}
```

Add `pyyaml` to runtime deps in `pyproject.toml` if not already present.

---

### 7 — `validate_contract.py` stub

**Current** ([src/utils/validate_contract.py](src/utils/validate_contract.py)): always returns `valid=True`.

**Docs** (`docs/CONTRIBUTING.md`): full implementation — loads manifests and Compose, checks:
1. Every manifest service exists in Compose
2. UID in Compose `user:` matches manifest `uid` (skip if no `user:` field set — not all services declare one)
3. Every manifest volume `path` appears in Compose `volumes:`

**Fix:** implement using docs' logic with one refinement: skip UID check when Compose service has no `user:` field (baikal, init, restic don't declare one — image default is acceptable for those services).

---

### 8 — `validate_no_duplicates.py` missing

Not present. Docs (`docs/CONTRIBUTING.md`) specifies it: detect keys declared in both `config/*.toml` and `ansible/group_vars/all.yml`, exit 1 if overlap found.

**Fix:** create `src/utils/validate_no_duplicates.py` from docs' implementation verbatim.

---

### 9 — `main.py` T0 gate incomplete

**Current** ([src/main.py](src/main.py)): calls `validate_manifest()` but never calls `validate_contract()`.

**Docs** architecture: T0 gate = `validate_manifest()` **and** `validate_contract()` before any command is issued.

**Fix:** after `validate_manifest()` passes, call `validate_contract(manifests, "docker-compose.yml")` and exit(1) on failure.

---

### 10 — `ValidationResult.errors` — keep current (richer)

**Current:** `errors: List[ContractViolation]` — structured with `service`, `field`, `message`.
**Docs:** `errors: list[str]` — plain strings.

**Decision:** keep current. `ContractViolation` carries more context and is already used in tests and `validate_manifest()`.

---

### 11 — `AppConfig` — keep current (more complete)

**Docs:** minimal (`env`, `log_level` only).
**Current:** adds `healthcheck_retries`, `healthcheck_interval_s`, `reconciler_max_retries` — all used.

**Decision:** keep current.

---

### 12 — `pyproject.toml` ruff and import-linter config

**Current:** no `[tool.ruff.lint]` section; import-linter has a placeholder comment.

**Docs** `[tool.ruff.lint]`:
```toml
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM"]
```
Note: docs also include `"D"` (docstrings). Since the current codebase has no docstrings on many functions, omit `"D"` initially and add it as a follow-up once functions are documented.

**Import-linter:** docs' contract in CONTRIBUTING.md is incorrect (forbids utils→models which is valid). Correct contracts per ARCHITECTURE.md:

```toml
[tool.importlinter]
root_package = "src"

[[tool.importlinter.contracts]]
name = "Reconciler must not import utils"
type = "forbidden"
source_modules = ["src.reconciler"]
forbidden_modules = ["src.utils"]

[[tool.importlinter.contracts]]
name = "Utils must not import reconciler"
type = "forbidden"
source_modules = ["src.utils"]
forbidden_modules = ["src.reconciler"]

[[tool.importlinter.contracts]]
name = "Models must not import anything internal"
type = "forbidden"
source_modules = ["src.models"]
forbidden_modules = ["src.reconciler", "src.utils"]
```

---

### 13 — `.editorconfig` missing

Create from docs — enforces LF line endings, UTF-8, trailing whitespace trimming, indent style per file type.

---

### 14 & 15 — `.vscode/settings.json` and `tasks.json` missing

Create both from docs. `tasks.json` adds three VS Code tasks:
- **Validate: Service Contract** — runs `validate_contract.py`, fires on folder open
- **Test: Molecule** — runs `molecule test`
- **Check: Complexity** — runs lizard with problem matcher

---

### 16 — Pre-commit missing contract and duplicate-value hooks

Add to `.pre-commit-config.yaml`:
```yaml
- id: contract-validation
  name: Service contract validation
  entry: .venv/bin/python -m src.utils.validate_contract
  language: system
  pass_filenames: false

- id: duplicate-values
  name: Duplicate value check
  entry: .venv/bin/python -m src.utils.validate_no_duplicates
  language: system
  pass_filenames: false
```

---

## Execution order

Changes are coupled — apply in this order to keep tests passing at each step:

1. `src/models/service.py` — optional fields (isolated, small)
2. `src/models/manifest.py` — `read_access` validator (isolated, small)
3. `src/models/state.py` — `SystemState` flat fields + `TransitionMap` Pydantic multi-path
4. `src/reconciler/observer.py` — update `from_label()` call sites for new field names
5. `src/reconciler/transitions.py` — return `TransitionMap()` instead of raw dict
6. `src/reconciler/controller.py` — use `next_toward()` instead of `.get()`
7. `tests/` — update model tests for new `SystemState` field names
8. `src/utils/ansible.py` — `AnsibleHost`, implement `load_manifests()`
9. `src/utils/validate_contract.py` — implement
10. `src/utils/validate_no_duplicates.py` — create
11. `src/main.py` — complete T0 gate
12. `pyproject.toml` — ruff lint rules, importlinter contracts
13. `.editorconfig` — create
14. `.vscode/settings.json`, `.vscode/tasks.json` — create
15. `.pre-commit-config.yaml` — add hooks

## Verification

```bash
pytest -v                                        # all tests pass after each step
pyright src/                                     # no new type errors
ruff check src/                                  # passes new lint rules
lint-imports                                     # import boundaries hold
python -m src.utils.validate_contract            # exits 0 against current compose
python -m src.utils.validate_no_duplicates       # exits 0 (no config/group_vars overlap)
python -m src.main                               # reconciler runs end-to-end
```
