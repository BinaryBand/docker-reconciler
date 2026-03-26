# Models Reference

## ServiceManifest
- service: str
- uid: int
- user: str
- volumes: list[VolumeSpec]
- read_access: list[str]

## VolumeSpec
- name: str
- path: str
- mode: str (octal)

## StateLabel (Enum: T0-T5, F1-F5)
## SystemState
- label: StateLabel
- steps: dict[str, bool]

## ContractViolation
- service: str
- field: str
- message: str

## ValidationResult
- valid: bool
- errors: list[ContractViolation]
