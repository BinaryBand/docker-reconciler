# Data Models

All Pydantic models used in the project. Every value crossing a module boundary must be one of these models or a typed primitive. Raw data is coerced at ingestion and never passed further.

See `ARCHITECTURE.md` for module ownership and import boundaries.

* * *

## Manifest Models

Owned by `models/manifest.py`. Ingested from `ansible/manifests/<service>.yml` by `utils/ansible.py`.

```python
from pydantic import BaseModel, field_validator


class VolumeSpec(BaseModel):
    name: str
    path: str
    mode: str

    @field_validator("mode")
    @classmethod
    def valid_mode(cls, v: str) -> str:
        if not v.startswith("0") or not all(c in "01234567" for c in v[1:]):
            raise ValueError(f"invalid octal mode: {v}")
        return v


class ServiceManifest(BaseModel):
    service: str
    uid: int
    user: str
    volumes: list[VolumeSpec]
    read_access: list[str] = []

    @field_validator("read_access")
    @classmethod
    def no_self_reference(cls, v: list[str], info: Any) -> list[str]:
        user = info.data.get("user")
        if user and user in v:
            raise ValueError(f"service cannot grant read access to itself: {user}")
        return v
```

* * *

## State Models

Owned by `models/state.py`. Used by `reconciler/` to represent and advance system state.

```python
from enum import Enum
from pydantic import BaseModel


class StateLabel(str, Enum):
    T0 = "T0"   # clean slate — manifest validation gate
    T1 = "T1"   # volumes provisioned
    T2 = "T2"   # permissions and ACLs applied
    T3 = "T3"   # services up
    T4 = "T4"   # post-start hooks complete
    T5 = "T5"   # health checks passing — desired state
    F1 = "F1"   # volume provisioning failed
    F2 = "F2"   # permissions failed
    F3 = "F3"   # compose failed
    F4 = "F4"   # post-start failed
    F5 = "F5"   # health checks failed


class SystemState(BaseModel):
    label: StateLabel
    volumes: bool = False
    permissions: bool = False
    compose: bool = False
    post_start: bool = False
    health: bool = False


class TransitionMap(BaseModel):
    transitions: dict[StateLabel, list[StateLabel]] = {
        StateLabel.T0: [StateLabel.T1],
        StateLabel.T1: [StateLabel.T2, StateLabel.F1, StateLabel.T0],
        StateLabel.T2: [StateLabel.T3, StateLabel.F2, StateLabel.T0],
        StateLabel.T3: [StateLabel.T4, StateLabel.F3, StateLabel.T0],
        StateLabel.T4: [StateLabel.T5, StateLabel.F4, StateLabel.T0],
        StateLabel.T5: [StateLabel.T0],
        StateLabel.F1: [StateLabel.T0],
        StateLabel.F2: [StateLabel.T0],
        StateLabel.F3: [StateLabel.T0],
        StateLabel.F4: [StateLabel.T0],
        StateLabel.F5: [StateLabel.T0],
    }

    def next_toward(
        self, current: StateLabel, desired: StateLabel
    ) -> StateLabel | None:
        """Return the next legal state toward desired, or None if no path exists."""
        legal = self.transitions.get(current, [])
        if desired in legal:
            return desired
        # Return the first forward step (non-failure, non-reset)
        forward = [s for s in legal if not s.startswith("F") and s != StateLabel.T0]
        return forward[0] if forward else None
```

* * *

## Contract Models

Owned by `models/contract.py`. Used by `utils/validate_manifest.py` and `utils/validate_contract.py`.

```python
from pydantic import BaseModel


class ContractViolation(BaseModel):
    service: str
    field: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ContractViolation] = []


class ComposeDef(BaseModel):
    """Typed representation of a docker-compose.yml service block."""
    name: str
    image: str
    user: str
    volumes: list[str]
```

* * *

## Config Models

Owned by `utils/config.py`. Ingested from `config/{env}.toml` at startup.

```python
from pydantic import BaseModel


class AppConfig(BaseModel):
    """Runtime config consumed by Python only. No infrastructure, no secrets."""
    env: str
    log_level: str = "INFO"
    healthcheck_retries: int = 3
    healthcheck_interval_s: int = 10
    reconciler_max_retries: int = 10
```

* * *

## Reconciler Models

Owned by `reconciler/model.py`. Used by `main.py` to configure the reconciler at startup.

```python
from pydantic import BaseModel
from models.state import StateLabel, TransitionMap


class ReconcilerConfig(BaseModel):
    desired_state: StateLabel
    transition_map: TransitionMap
    max_retries: int = 3
    dry_run: bool = False
```

* * *

## Service & Container Models

Owned by `models/service.py`. Used by `reconciler/observer.py` to represent observed runtime state.

```python
from pydantic import BaseModel


class ContainerState(BaseModel):
    """Observed runtime state of a single container — reported by Compose, never queried directly."""
    service: str
    running: bool
    healthy: bool | None = None
    exit_code: int | None = None


class ClusterState(BaseModel):
    """Observed state of all containers at a given reconciliation step."""
    containers: list[ContainerState]

    def all_running(self) -> bool:
        return all(c.running for c in self.containers)

    def all_healthy(self) -> bool:
        return all(c.healthy is True for c in self.containers)
```

* * *

## Ansible Models

Owned by `utils/ansible.py`. Coerced immediately at ingestion — raw subprocess output never leaves this module.

```python
from pydantic import BaseModel


class AnsibleHost(BaseModel):
    ansible_host: str
    ansible_user: str | None = None


class AnsibleInventory(BaseModel):
    """Typed representation of ansible-inventory --list output."""
    hosts: dict[str, AnsibleHost] = {}
    vars: dict[str, str] = {}
```
