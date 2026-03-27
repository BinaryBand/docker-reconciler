from pydantic import BaseModel


class ContractViolation(BaseModel):
    service: str
    field: str
    message: str


class ValidationResult(BaseModel):
    valid: bool
    errors: list[ContractViolation]


class ComposeDef(BaseModel):
    name: str
    image: str
    user: str
    volumes: list[str]
